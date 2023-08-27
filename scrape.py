import re
import asyncio
from typing import Literal

from tqdm import tqdm
from aiohttp import ClientSession
from bs4 import BeautifulSoup as BS, ResultSet, Tag

base_url = 'https://www2.eecs.berkeley.edu'
courses_url = f'{base_url}/Courses/{{}}'
departments = ['EE', 'CS']

pattern_100_series = r'\b\w+\s?(?:1[0-9][0-9])\b'
pattern_200_series = r'\b\w+\s?(?:2[0-8][0-9]|29[0-79])\b'

title_set: set[str] = set()
ignored_courses = {}
course_series: dict[Literal[100, 200], list[str, str, int, str]] = {
    100: [],
    200: [],
}


async def fetch_soup(session, url):
    async with session.get(url) as response:
        return BS(await response.text(), 'html.parser')


async def scrape_courses(session: ClientSession, department: str):
    soup = await fetch_soup(session, courses_url.format(department))

    # with open(f'./Berkeley_EECS_2023_Schedules/{department}.md', 'w', encoding='utf-8') as file:
    content_div: Tag = soup.find('div', class_='content')
    lis: ResultSet[Tag] = content_div.find_all('li')

    for li in tqdm(lis):
        if not isinstance(li.a, Tag):
            continue

        number, title = li.a.get_text(strip=True).split('. ')

        if re.match(pattern_100_series, number):
            series = 100
        elif re.match(pattern_100_series, number):
            series = 200
        else:
            continue

        if title in title_set or title in ignored_courses:
            continue

        print(title)

        if not isinstance(li.p, Tag):
            continue

        # Extracting the description
        desc_start = li.p.find('strong', string='Catalog Description:').next_sibling
        desc_end = li.p.find('br')
        desc = ''.join(
            str(item)
            for item in li.p.contents[
                li.p.contents.index(desc_start) : li.p.contents.index(desc_end)
            ]
        ).strip()

        # Extracting the units
        unit_start = li.p.find('strong', string='Units:').next_sibling
        unit = unit_start.strip()

        title_set.add(title)
        course_series[series].append((number, title, unit, desc))


async def main():
    async with ClientSession() as session:
        tasks = [scrape_courses(session, d) for d in departments]
        await asyncio.gather(*tasks)

        for series, courses in course_series.items():
            with open(f'./Berkeley_EECS_Courses/{series}.md', 'w', encoding='utf-8') as file:
                for i, (number, title, unit, desc) in enumerate(courses, 1):
                    file.write(f'{i}. **{number} - {title}** ({unit} unit)\n{desc}\n\n')

        # for d, courses in zip(departments, results):
        #     print(f"Department {d} Schedule:")
        #     for _, title, desc in courses:
        #         print(f'{title}\n{desc}\n')
        #     print('\n')


if __name__ == '__main__':
    asyncio.run(main())

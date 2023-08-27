import asyncio
from tqdm import tqdm
from aiohttp import ClientSession
from bs4 import BeautifulSoup as BS, ResultSet, Tag

base_url = 'https://www2.eecs.berkeley.edu'
schedule_url = f'{base_url}/Scheduling/{{}}/schedule.html'
departments = ['EE', 'CS']

ignored_courses = {}


async def fetch_soup(session, url):
    async with session.get(url) as response:
        return BS(await response.text(), 'html.parser')


async def scrape_course_desc(session: ClientSession, url: str) -> str:
    soup = await fetch_soup(session, url)

    # Find the content div and then extract the text of the first p tag inside it
    content_div: Tag = soup.find('div', class_='content')
    if content_div and isinstance(content_div.p, Tag):
        return content_div.p.get_text(strip=True)
    return ""


async def scrape_schedule(session: ClientSession, department: str):
    soup = await fetch_soup(session, schedule_url.format(department))

    with open(f'./Berkeley_EECS_2023_Schedules/{department}.md', 'w') as file:
        rows: ResultSet[Tag] = soup.find_all('tr', class_='primary')
        course_title_set: set[str] = set()
        courses: list[tuple[str, str, str]] = []

        for row in tqdm(rows):
            tds: ResultSet[Tag] = row.find_all('td')
            if len(tds) < 4:  # ensure there are at least 5 td elements
                continue

            course_title = tds[3].get_text(strip=True)
            if course_title in course_title_set:
                continue

            th = row.find('th')
            if th is None or not isinstance(th.a, Tag):
                continue

            course_number = th.get_text(strip=True)

            course_url = th.a['href']
            # fetch from course url: I want the text in the first <p> within <div class="content">. The text will be assigned to course_decs
            course_desc = await scrape_course_desc(session, f'{base_url}/{course_url}')

            course_title_set.add(course_title)
            courses.append((course_number, course_title, course_desc))

            file.write(f"## {course_title}\n{course_desc}\n")

    return courses


async def main():
    async with ClientSession() as session:
        tasks = [scrape_schedule(session, d) for d in departments]
        results: list[tuple[str, str, str]] = await asyncio.gather(*tasks)

        for d, courses in zip(departments, results):
            print(f"Department {d} Schedule:")
            for _, title, desc in courses:
                print(f'{title}\n{desc}\n')
            print('\n')


if __name__ == '__main__':
    asyncio.run(main())

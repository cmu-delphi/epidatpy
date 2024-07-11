from asyncio import get_event_loop

from epidatpy.async_request import Epidata


async def main() -> None:
    apicall = Epidata.covidcast("fb-survey", "smoothed_cli", "day", "nation", Epidata.range(20210405, 20210410), "us")
    classic = await apicall.classic()
    print(classic)

    r = await apicall.csv()
    print(r[0:100])

    data = await apicall.json()
    print(data[0])

    async for row in apicall.iter():
        print(row)


loop = get_event_loop()
loop.run_until_complete(main())

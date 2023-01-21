import traceback
from pprint import pprint

import aiofiles
import aiohttp
import logging


def is_dev(ctx):
    return ctx.author.id in [465129603208577044]


def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:-1])
    # remove `foo`
    return content.strip("` \n")


def get_traceback(error):
    etype = type(error)
    trace = error.__traceback__
    verbosity = 10
    lines = traceback.format_exception(etype, error, trace, verbosity)
    txt = "\n".join(lines)

    return txt


def textSlicer(text, maxchars: int = 2000):
    s = 0
    es = maxchars
    res = []
    while s < len(text):
        res.append(text[s:es])
        s += maxchars
        es += maxchars
        if len(text) < es:
            es = len(text)

    return res


# with open("labels.json", "r") as f:
#     labels = load(f)
#     pprint(labels)
#
#
# def getAllLabels():
#     return labels


async def postAPI(endpoint, infos={}, *, api):
    headers = {
        "X-Api-Auth": api,
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(
            "https://labelsupply.io/api/order/" + endpoint, data=infos
        ) as resp:
            logging.info(resp.status)
            logging.info(await resp.text())
            logging.info(await resp.json())

    return (resp.status, await resp.json())


async def getAPI(endpoint, *, api):
    headers = {
        "X-Api-Auth": api,
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get("https://labelsupply.io/api/order/" + endpoint) as resp:
            logging.info(resp.status)
            logging.info(await resp.json())

    return await resp.json()


async def getConfig():
    return await getAPI("config", api="33becc87-f32c-d3da-d9df-d9befd2eba25")


async def createLabel(interaction, infos):
    guild_id = interaction.guild.id
    api_key = (await interaction.client.sql.get_api_key(guild_id))[0]["api_key"]
    # return {
    #     "Data": {
    #         "Order": {
    #             "Added": 1657136410,
    #             "AddedFormatted": "07/06/2022 19:40",
    #             "Cancellable": False,
    #             "Downloadable": False,
    #             "Duplicatable": True,
    #             "ExternalID": "cc7f2ffb-947c-b269-b844-fa56f00d4ef1",
    #             "FromCity": "",
    #             "FromCompany": "Testing",
    #             "FromCountry": "1657136409",
    #             "FromFormatted": "France Testing AA",
    #             "FromName": "France",
    #             "FromPhone": "0552922142",
    #             "FromState": "Testing",
    #             "FromStreet": "0",
    #             "FromStreet2": "Testing",
    #             "FromZip": "AA",
    #             "ID": "e5fd36d3-750b-080f-3c4c-2e78eef36ab1",
    #             "Modified": 1657136410,
    #             "ModifiedFormatted": "07/06/2022 19:40",
    #             "Notes": "",
    #             "Price": 3,
    #             "PriceFormatted": "$3.00",
    #             "Refundable": True,
    #             "Status": 0,
    #             "StatusName": "New",
    #             "ToCity": "",
    #             "ToCompany": "Testing",
    #             "ToCountry": "Testing",
    #             "ToFormatted": "France Testing AA",
    #             "ToName": "France",
    #             "ToPhone": "3225101252",
    #             "ToState": "Testing",
    #             "ToStreet": "0",
    #             "ToStreet2": "Testing",
    #             "ToZip": "AA",
    #             "TrackLink": "https://tools.usps.com/go/TrackConfirmAction?tLabels=",
    #             "Trackable": False,
    #             "Tracking": "",
    #             "Type": "23f036ee-d8c4-4cef-a5eb-6423b33b754d",
    #             "TypeName": "USPS First Class V4",
    #             "User": "d94c39e0-7a04-7d41-d069-1c464b8944f0",
    #             "Username": "Gugu72",
    #             "Weight": 1,
    #             "WeightFormatted": "1 lb",
    #         }
    #     },
    #     "Error": "",
    #     "Success": True,
    # }
    logging.warning("###CREATING LABEL###")
    logging.warning(infos)
    return await postAPI("", infos, api=api_key)


async def getPDF(order_id, *, api):
    headers = {
        "X-Api-Auth": api,
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(
            "https://labelsupply.io/api/order/" + str(order_id) + "/file"
        ) as resp:
            if resp.status == 200:
                # print(await resp.text())
                content = await resp.content.read()
            else:
                print(resp.content_type)
                if resp.content_type == "application/json":
                    r = await resp.json()
                else:
                    r = await resp.text()
                pprint(r)
                return (resp.status, r)
        async with aiofiles.open(f"tmp/{order_id}.pdf", "wb") as f:
            await f.write(content)
    return (resp.status, f"tmp/{order_id}.pdf")

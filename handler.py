from fastapi import FastAPI, Query
from mangum import Mangum
import pandas as pd
from difflib import get_close_matches

df = pd.read_csv("postalcodes.csv")
df.fillna("", inplace=True)
df["SUBURB"] = df["SUBURB"].str.lower().str.strip()
df["AREA"] = df["AREA"].str.lower().str.strip()

app = FastAPI()

@app.get("/autocomplete")
def autocomplete(query: str = Query(..., min_length=2)):
    query = query.lower()
    matches = df[df["SUBURB"].str.contains(query) | df["AREA"].str.contains(query)].head(10)
    return {
        "results": [
            {
                "suburb": row["SUBURB"].title(),
                "area": row["AREA"].title(),
                "street_code": row["STR-CODE"],
                "box_code": row["BOX-CODE"]
            }
            for _, row in matches.iterrows()
        ]
    }

@app.get("/validate")
def validate(suburb: str = "", area: str = ""):
    suburb, area = suburb.lower().strip(), area.lower().strip()
    exact = df[(df["SUBURB"] == suburb) & (df["AREA"] == area)]
    if not exact.empty:
        r = exact.iloc[0]
        return {
            "valid": True,
            "details": {
                "suburb": r["SUBURB"].title(),
                "area": r["AREA"].title(),
                "street_code": r["STR-CODE"],
                "box_code": r["BOX-CODE"]
            }
        }

    partial = df[df["SUBURB"].str.contains(suburb) & df["AREA"].str.contains(area)]
    if not partial.empty:
        return {
            "valid": False,
            "message": "No exact match, but here are similar results.",
            "suggestions": [
                {
                    "suburb": row["SUBURB"].title(),
                    "area": row["AREA"].title(),
                    "street_code": row["STR-CODE"],
                    "box_code": row["BOX-CODE"]
                }
                for _, row in partial.head(5).iterrows()
            ]
        }

    fuzzy = df[
        df["SUBURB"].isin(get_close_matches(suburb, df["SUBURB"], n=3, cutoff=0.6)) &
        df["AREA"].isin(get_close_matches(area, df["AREA"], n=3, cutoff=0.6))
    ]
    return {
        "valid": False,
        "message": "No match found for the provided suburb and area.",
        "suggestions": [
            {
                "suburb": row["SUBURB"].title(),
                "area": row["AREA"].title(),
                "street_code": row["STR-CODE"],
                "box_code": row["BOX-CODE"]
            }
            for _, row in fuzzy.head(5).iterrows()
        ]
    }

handler = Mangum(app)

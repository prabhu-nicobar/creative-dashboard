"""Ad Nomenclature — hard-coded attribute table.

Extracted from the 'Ad Nomenclature Lifetime' sheet in project knowledge. Only rows
carrying an actual Ad Name are here; blank-name rows are briefs that never went live
and have nothing to join against.

Primary variable string is Funnel_Category_Destination_Angle_Format.
The FUNNEL position is deliberately NOT used — funnel stage always comes from the
campaign (see V2 scope item 2). Angle is the value this table exists for.

Join key is the ad name lower-cased with whitespace collapsed, because the sheet and
Meta disagree on spacing in several places ('SNG-WW-Costa Pants -PDP-190826').

To refresh: replace ROWS with the current sheet export. Columns, in order:
  primary_vars, ad_name, silhouette, subcategory, class, collection, vo, ai
"""
import re

ROWS = [
 ("TOF_WW_PDP_OCCN_SNG","SNG-WW-Godavari-V1-PLP-090826","New","Kurtas & Tunics","Kurtas","Godavari","Non-VO","Non-AI"),
 ("TOF_WW_PLP_TASTE_SNG","SNG-WW-Godavari-V2-PLP-090826","Adopted","Kurtas & Tunics","Kurtas","Godavari","Non-VO","Non-AI"),
 ("TOF_WW_PLP_OCCN_SNG","SNG-WW-Godavari-V3-PLP-090826","New","Kurtas & Tunics","Kurtas","Godavari","Non-VO","Non-AI"),
 ("TOF_MW_PLP_FORM_SNG","SNG-MW-Godavari-Bageecha-Kurta-PDP-090826","Adopted","Kurtas & Jackets","Kurtas","Godavari","Non-VO","Non-AI"),
 ("TOF_MW_PDP_TASTE_SNG","Carousel-MW-Yamuna-Bena-Shirt-PDP-100826","Adopted","Shirts","Shirts","Yamuna","Non-VO","Non-AI"),
 ("TOF_Gifting_PDP_TASTE_SNG","SNG-HH-Godavari-Zodiac-PDP-090826","New","Drinkware","Giftsets","Godavari","Non-VO","Non-AI"),
 ("TOF_WW_Col_FORM_Carousel","Carousel-WW-Godavari-Kurtas-PDP-030926","New","Kurtas & Tunics","Kurtas","Godavari","Non-VO","Non-AI"),
 ("TOF_MW_PDP_FORM_GIF","GIF-MW-Yamuna-Reversible-Shirt-PDP-090826","New","Shirts","Shirts","Yamuna","Non-VO","Non-AI"),
 ("TOF_MW_PDP_TASTE_Carousel","Carousel-MW-Shirts-Details-PDP-100826","Mix","Mix","Mix","Mix","Non-VO","Non-AI"),
 ("BOF_Gifting_PLP_RANGE_SNG","SNG-HH-Godavari-Wadi-Giftset-PLP-090826","Adopted","Drinkware","Giftsets","Godavari","Non-VO","Non-AI"),
 ("TOF_HH_PLP_TASTE_SNG","SNG-HH-Godavari-Fragrance-PLP-120826",None,"Fragrance","Mix","Godavari","Non-VO","Non-AI"),
 ("TOF_HH_PLP_OCCN_SNG","SNG-HH-Decor-Bookend-V2-PLP-120826",None,"Decor","Bookends","Core","Non-VO","Non-AI"),
 ("TOF_HH_PLP_CRAFT_SNG","SNG-HH-Brass-PLP-120826",None,"Dinnerware","Mix","Core","Non-VO","Non-AI"),
 ("TOF_HH_PDP_TASTE_SNG","SNG-HH-Brass-Gelato-PDP-AI-120826",None,"Serveware","Serving bowls","Core","Non-VO","AI"),
 ("TOF_HH_PDP_CRAFT_SNG","SNG-HH-Brass-SweetBegin-PDP-120826",None,"Serveware","Giftsets","Wedding edit","Non-VO","Non-AI"),
 ("BOF_HH_PDP_RANGE_SNG","SNG-HH-Gifting-Alphabet-PLP-120826",None,"Mix","Mix","Core","Non-VO","Non-AI"),
 ("TOF_HH_PLP_OCCN_SNG","SNG-HH-Ganga-Barware-PLP-120826",None,"Barware","Glasses","Ganga","Non-VO","Non-AI"),
 ("TOF_HH_PDP_TASTE_SNG","SNG-HH-Dinnerset-PLP-120826",None,"Dinnerware","Dinner sets","Yamuna","Non-VO","Non-AI"),
 ("TOF_WW_PLP_OCCN_Static","SNG-WW-Godavari-Hera halter kurta-PLP-190826","New","Kurtas & Tunics","Kurtas","Godavari","Non-VO","Non-AI"),
 ("TOF_WW_Mixed_VERS_Carousel","Carousel-WW-Yamuna- Smart-PDP-190826","Mix","Mix","Mix","Mix","Non-VO","Non-AI"),
 ("TOF_WW_PLP_VERS_Static","SNG-WW-Coords-Kolva Set-PLP-190826","New","Co-ords","Co-ords","Godavari","Non-VO","Non-AI"),
 ("BOF_WW_PDP_OCCN_Static","SNG-WW-Narsa Kurta-PDP-190826","New","Kurtas & Tunics","Kurtas","Godavari","Non-VO","Non-AI"),
 ("TOF_WW_PDP_FORM_Static","SNG-WW-Godavari-Kutch-Kurta-PDP-300826","New","Kurtas & Tunics","Kurtas","Godavari","Non-VO","Non-AI"),
 ("BOF_WW_PDP_CRAFT_Carousel","Carousel-WW-Godavari-Kurta-Print Story-PLP-190826","New","Kurtas & Tunics","Kurtas","Godavari","Non-VO","Non-AI"),
 ("TOF_WW_PDP_FORM_Video","Video-WW-Yamuna-Kinaar-Dress-AI-PDP-050926","New","Dresses & Jumpsuits","Dresses","Yamuna","Non-VO","AI"),
 ("TOF_WW_PDP_VERS_Carousel","Carousel-WW-workwear-PDP-190826","Mix","Mix","Mix","Mix","Non-VO","Non-AI"),
 ("TOF_WW_PDP_FORM_Carousel","Carousel-WW-Pants that Pair-PDP-190826","Mix","Mix","Mix","Mix","Non-VO","Non-AI"),
 ("BOF_WW_PDP_CRAFT_Static","SNG-WW-Costa Pants -PDP-190826","Adopted","Bottoms","Pants","Yamuna","Non-VO","Non-AI"),
 ("BOF_WW_PDP_CRAFT_Static","SNG-WW-Lazy Sunday Tunic-PDP-190826","Adopted","Kurtas & Tunics","Tunics","Godavari","Non-VO","Non-AI"),
 ("TOF_HH_PLP_TASTE_Static","SNG-HH-Drinkware-Espresso-PLP-190826",None,"Drinkware","Espresso mugs","Core","Non-VO","Non-AI"),
 ("TOF_HH_Mixed_TASTE_Carousel","Carousel-HH-Decor-PLP-190826",None,"Decor","Mix","Decor","Non-VO","Non-AI"),
 ("TOF_HH_PLP_OCCN_TBD","SNG-HH-Dining-PLP-190826",None,"Dinnerware","Mix","Core","Non-VO","Non-AI"),
 ("TOF_HH_PLP_VERS_Carousel","Carousel-HH-Dining-PLP-190826",None,"Dinnerware","Plates","Core","Non-VO","Non-AI"),
 ("TOF_HH_PDP_CRAFT_TBD","SNG-HH-Brass- Chand Spice Box-PDP-190826",None,"Kitchenware","Kitchen organisers","Core","Non-VO","Non-AI"),
 ("TOF_HH_PLP_TASTE_Static","SNG-HH-Zodiac series-PLP-190826",None,"Drinkware","Giftsets","Godavari","Non-VO","Non-AI"),
 ("TOF_HH_PLP_OCCN_TBD","SNG-HH-Barware-Mist Martini-PLP-190826",None,"Barware","Glasses","Ganga","Non-VO","Non-AI"),
 ("TOF_HH_PLP_OCCN_TBD","SNG-HH-Decor-ele palm votive-PLP-190826",None,"Decor","Votives & Candleholders","Core","Non-VO","Non-AI"),
 ("TOF_Gifting_TBD_OCCN_TBD","SNG-Gifting-Rakhi-Ceylong lush gift set--190826","Adopted","Drinkware","Giftsets","Godavari","Non-VO","Non-AI"),
 ("TOF_Gifting_TBD_OCCN_Static","SNG-Gifting-Mehfil bar gift set-PDP-190826","New","Barware","Giftsets","Godavari","Non-VO","Non-AI"),
 ("TOF_Gifting_Mixed_OCCN_Carousel","Carousel-Gifting-Best of nicobar gifts-PLP-190826","Mix","Mix","Giftsets","Mix","Non-VO","Non-AI"),
 ("BOF_MW_PLP_CRAFT_Static","SNG-MW-Godavari-Zenith-Kurta-PDP-260826","Adopted","Kurtas & Jackets","Kurtas","Godavari","Non-VO","Non-AI"),
 ("TOF_MW_PDP_FORM_Static","SNG-MW-Yamuna-Dune-Shacket-PDP-260826","New","Kurtas & Jackets","Jackets","Yamuna","Non-VO","Non-AI"),
 ("TOF_MW_PLP_TASTE_Static","SNG-MW-Godavari-Rayh-Shacket-PLP-270826","New","Kurtas & Jackets","Jackets","Godavari","Non-VO","Non-AI"),
 ("TOF_MW_PDP_FORM_Static","SNG-MW-Yamuna-Breeze-Trouser-PDP-260826","New","Bottomwear","Trousers","Godavari","Non-VO","Non-AI"),
 ("TOF_MW_PLP_FORM_Static","SNG-MW-Godavari-Mistari-Shirt-PDP-280826","Adopted","Shirts","Shirts","Godavari","Non-VO","Non-AI"),
 ("TOF_MW_PDP_FORM_Static","SNG-MW-Yamuna-Abeer-Polo-PDP-280826","New","T-shirts","T-shirts","Yamuna","Non-VO","Non-AI"),
 ("TOF_MW_PLP_VERS_Static","SNG-MW-Yamuna-Denim-Shirt-PDP-270826","Adopted","Shirts","Shirts","Yamuna","Non-VO","Non-AI"),
]

ANGLE_LABELS = {"OCCN": "Occasion", "TASTE": "Taste", "FORM": "Form",
                "CRAFT": "Craft", "RANGE": "Range", "VERS": "Versatility"}

def key(name):
    """Normalise for joining — the sheet and Meta disagree on spacing and case."""
    return re.sub(r"[\s\-]+", "-", (name or "").strip().lower()).strip("-")

# Meta prefixes every ad name with its campaign and ad set — 'NB-011-A01-SNG-HH-...'
# while the sheet stores only the creative part, 'SNG-HH-...'. Strip the prefix.
PREFIX = re.compile(r"^(nb|fe|et|th)-\d+-a\d+-", re.I)

def lookup(name, table=None):
    """Match a Meta ad name against the sheet, tolerating the campaign prefix."""
    table = TABLE if table is None else table
    k = key(name)
    if k in table: return table[k]
    stripped = PREFIX.sub("", k)
    if stripped in table: return table[stripped]
    # last resort: longest suffix match, so a trailing date edit still joins
    for cand in table:
        if stripped.startswith(cand) or cand.startswith(stripped):
            if abs(len(cand) - len(stripped)) <= 8:
                return table[cand]
    return {}

def build():
    out = {}
    for primary, name, sil, sub, cls, coll, vo, ai in ROWS:
        if not name: continue
        parts = primary.split("_")
        angle = ANGLE_LABELS.get(parts[3], parts[3]) if len(parts) >= 5 else None
        out[key(name)] = dict(angle=angle, silhouette=sil, subcategory=sub,
                              **{"class": cls}, collection_sheet=coll, vo=vo, ai=ai)
    return out

TABLE = build()

if __name__ == "__main__":
    print(f"{len(TABLE)} tagged ad names")
    from collections import Counter
    for f in ("angle", "silhouette", "vo", "ai"):
        print(f"  {f}: {dict(Counter(v[f] for v in TABLE.values()))}")

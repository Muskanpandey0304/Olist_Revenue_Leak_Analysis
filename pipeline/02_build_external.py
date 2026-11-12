"""Build external reference tables.

ibge_states_2018.csv
  population : IBGE estimated resident population, reference date 1 July 2018
               (estimativa_dou_2018, published 2018-10-19, table "Brasil e Unidades da Federacao")
  income_pc  : IBGE PNAD Continua 2018, nominal monthly household income per capita (R$),
               release of 27 Feb 2019 (Rendimento domiciliar per capita 2018)

holidays_brazil.csv
  National public holidays, 2016-2018, from the `holidays` package.
"""
from pathlib import Path
import pandas as pd
import holidays

OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "external"

# state_code, state_name, region, population (1 Jul 2018), income per capita (R$, 2018)
STATES = [
    ("RO", "Rondonia", "North", 1757589, 1113), ("AC", "Acre", "North", 869265, 909),
    ("AM", "Amazonas", "North", 4080611, 791), ("RR", "Roraima", "North", 576568, 1204),
    ("PA", "Para", "North", 8513497, 863), ("AP", "Amapa", "North", 829494, 857),
    ("TO", "Tocantins", "North", 1555229, 1045),
    ("MA", "Maranhao", "Northeast", 7035055, 605), ("PI", "Piaui", "Northeast", 3264531, 817),
    ("CE", "Ceara", "Northeast", 9075649, 855), ("RN", "Rio Grande do Norte", "Northeast", 3479010, 956),
    ("PB", "Paraiba", "Northeast", 3996496, 898), ("PE", "Pernambuco", "Northeast", 9496294, 871),
    ("AL", "Alagoas", "Northeast", 3322820, 714), ("SE", "Sergipe", "Northeast", 2278308, 906),
    ("BA", "Bahia", "Northeast", 14812617, 841),
    ("MG", "Minas Gerais", "Southeast", 21040662, 1322), ("ES", "Espirito Santo", "Southeast", 3972388, 1295),
    ("RJ", "Rio de Janeiro", "Southeast", 17159960, 1689), ("SP", "Sao Paulo", "Southeast", 45538936, 1898),
    ("PR", "Parana", "South", 11348937, 1607), ("SC", "Santa Catarina", "South", 7075494, 1660),
    ("RS", "Rio Grande do Sul", "South", 11329605, 1705),
    ("MS", "Mato Grosso do Sul", "Center-West", 2748023, 1439), ("MT", "Mato Grosso", "Center-West", 3441998, 1386),
    ("GO", "Goias", "Center-West", 6921161, 1323), ("DF", "Distrito Federal", "Center-West", 2974703, 2460),
]
states = pd.DataFrame(STATES, columns=["state_code", "state_name", "region", "population", "income_pc"])

# Source totals used as a check on the transcription
assert len(states) == 27 and states.state_code.is_unique
assert states.population.sum() == 208_494_900, states.population.sum()
region_totals = {"North": 18_182_253, "Northeast": 56_760_780, "Southeast": 87_711_946,
                 "South": 29_754_036, "Center-West": 16_085_885}
for reg, tot in region_totals.items():
    assert states.loc[states.region == reg, "population"].sum() == tot, reg
states.to_csv(OUT / "ibge_states_2018.csv", index=False)

hol = holidays.Brazil(years=[2016, 2017, 2018])
pd.DataFrame(sorted(hol.items()), columns=["date", "holiday_name"]).to_csv(OUT / "holidays_brazil.csv", index=False)
print("states:", len(states), "| population total:", f"{states.population.sum():,}", "(matches IBGE Brasil total and all 5 regions)")
print("holidays:", len(hol))

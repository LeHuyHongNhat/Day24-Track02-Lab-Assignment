# scripts/generate_data.py
import pandas as pd
from faker import Faker
import random
import os

fake = Faker("vi_VN")
Faker.seed(42)


def generate_patients(n=200):
    records = []
    for _ in range(n):
        # Clean names and addresses: replace commas and newlines to avoid CSV corruption
        ho_ten = fake.name().replace(",", "").replace("\n", " ")
        dia_chi = fake.address().replace(",", " ").replace("\n", " ")
        bac_si = fake.name().replace(",", "").replace("\n", " ")

        records.append({
            "patient_id": fake.uuid4(),
            "ho_ten": ho_ten,
            "cccd": str(random.randint(1, 9))
                    + "".join([str(random.randint(0, 9)) for _ in range(11)]),
            "ngay_sinh": fake.date_of_birth(minimum_age=18, maximum_age=90)
            .strftime("%d/%m/%Y"),
            "so_dien_thoai": "0" + str(random.choice([3, 5, 7, 8, 9]))
            + "".join([str(random.randint(0, 9)) for _ in range(8)]),
            "email": fake.email(),
            "dia_chi": dia_chi,
            "benh": random.choice(["Tiểu đường", "Huyết áp cao",
                                   "Tim mạch", "Khỏe mạnh"]),
            "ket_qua_xet_nghiem": round(random.uniform(3.5, 12.0), 2),
            "bac_si_phu_trach": bac_si,
            "ngay_kham": fake.date_this_year().strftime("%d/%m/%Y"),
        })
    return pd.DataFrame(records)


df = generate_patients()
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
df.to_csv("data/raw/patients_raw.csv", index=False)
print(f"Generated {len(df)} patient records")
print(df.head(3))

def read_float(prompt):
    while True:
        try:
            return float(input(prompt).replace(",", "."))
        except ValueError:
            print("Valoare invalidă. Încearcă din nou.")


def calc_salary(
    gross_salary,
    total_hours,
    night_hours,
    weekend_hours,
    night_bonus_percent,
    weekend_bonus_percent,
    other_bonus_value=0,
    other_bonus_percent=0,
):
    if total_hours <= 0:
        raise ValueError("Orele totale trebuie să fie > 0.")

    hourly_rate = gross_salary / total_hours

    # Sporuri
    night_bonus = night_hours * hourly_rate * (night_bonus_percent / 100)
    weekend_bonus = weekend_hours * hourly_rate * (weekend_bonus_percent / 100)

    # Alte sporuri (fix + procent)
    other_bonus = other_bonus_value + (gross_salary * other_bonus_percent / 100)

    total_gross = gross_salary + night_bonus + weekend_bonus + other_bonus

    # Taxe România
    cas = total_gross * 0.25
    cass = total_gross * 0.10
    taxable = total_gross - cas - cass
    tax = taxable * 0.10

    net = total_gross - cas - cass - tax

    return {
        "Tarif orar brut": hourly_rate,
        "Spor noapte": night_bonus,
        "Spor weekend": weekend_bonus,
        "Alte sporuri": other_bonus,
        "Brut total": total_gross,
        "CAS": cas,
        "CASS": cass,
        "Impozit": tax,
        "Net": net,
        "Tarif orar net": net / total_hours,
    }


def main():
    print("=== Calculator salariu ===\n")

    gross_salary = read_float("Salariu brut: ")
    total_hours = read_float("Total ore lucrate: ")

    night_hours = read_float("Ore de noapte: ")
    night_bonus_percent = read_float("Spor noapte (%): ")

    weekend_hours = read_float("Ore weekend: ")
    weekend_bonus_percent = read_float("Spor weekend (%): ")

    print("\n--- Alte sporuri ---")
    other_bonus_value = read_float("Sumă fixă (0 dacă nu există): ")
    other_bonus_percent = read_float("Procent din salariu (%): ")

    result = calc_salary(
        gross_salary,
        total_hours,
        night_hours,
        weekend_hours,
        night_bonus_percent,
        weekend_bonus_percent,
        other_bonus_value,
        other_bonus_percent,
    )

    print("\n=== REZULTATE ===")
    for k, v in result.items():
        print(f"{k}: {v:.2f}")


if __name__ == "__main__":
    main()

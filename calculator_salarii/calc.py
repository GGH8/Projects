def read_float(prompt):
    while True:
        try:
            return float(input(prompt).replace(",", ".").strip())
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
    meal_tickets_value=0,
    cultural_tickets_value=0,
    meal_tickets_tax_percent=19,
    cultural_tickets_tax_percent=10,
):
    if total_hours <= 0:
        raise ValueError("Numărul total de ore trebuie să fie mai mare decât 0.")

    if night_hours < 0 or weekend_hours < 0:
        raise ValueError("Orele de noapte și de weekend nu pot fi negative.")

    if night_hours + weekend_hours > total_hours:
        raise ValueError("Orele de noapte + orele de weekend nu pot depăși totalul orelor lucrate.")

    hourly_rate = gross_salary / total_hours

    # Sporuri
    night_bonus = night_hours * hourly_rate * (night_bonus_percent / 100)
    weekend_bonus = weekend_hours * hourly_rate * (weekend_bonus_percent / 100)
    other_bonus = other_bonus_value + (gross_salary * other_bonus_percent / 100)

    # Brut total
    total_gross = gross_salary + night_bonus + weekend_bonus + other_bonus

    # Taxe salariale
    cas = total_gross * 0.25
    cass = total_gross * 0.10
    taxable_income = total_gross - cas - cass
    income_tax = taxable_income * 0.10

    # Net înainte de bonuri
    net_before_ticket_taxes = total_gross - cas - cass - income_tax

    # Rețineri din cauza bonurilor
    meal_tickets_tax = meal_tickets_value * (meal_tickets_tax_percent / 100)
    cultural_tickets_tax = cultural_tickets_value * (cultural_tickets_tax_percent / 100)
    total_ticket_taxes = meal_tickets_tax + cultural_tickets_tax

    # Net final corect
    final_net_salary = net_before_ticket_taxes - total_ticket_taxes

    # Tarif orar
    gross_hourly_rate = total_gross / total_hours
    net_hourly_rate = final_net_salary / total_hours

    return {
        "Tarif orar brut": hourly_rate,
        "Spor noapte": night_bonus,
        "Spor weekend": weekend_bonus,
        "Alte sporuri": other_bonus,
        "Brut total": total_gross,
        "CAS": cas,
        "CASS": cass,
        "Bază impozabilă": taxable_income,
        "Impozit pe venit": income_tax,
        "Net înainte de reținerea bonurilor": net_before_ticket_taxes,
        "Taxă bonuri de masă": meal_tickets_tax,
        "Taxă bonuri culturale": cultural_tickets_tax,
        "Total rețineri bonuri": total_ticket_taxes,
        "Net salarial final": final_net_salary,
        "Tarif orar brut efectiv": gross_hourly_rate,
        "Tarif orar net efectiv": net_hourly_rate,
    }


def print_results(results):
    print("\n=== REZULTATE ===")
    for key, value in results.items():
        print(f"{key}: {value:.2f} RON")


def main():
    print("=== Calculator salariu + sporuri + rețineri bonuri ===\n")

    gross_salary = read_float("Introdu salariul brut: ")
    total_hours = read_float("Introdu numărul total de ore lucrate: ")

    night_hours = read_float("Introdu numărul de ore de noapte: ")
    night_bonus_percent = read_float("Introdu sporul de noapte (%): ")

    weekend_hours = read_float("Introdu numărul de ore de weekend: ")
    weekend_bonus_percent = read_float("Introdu sporul de weekend (%): ")

    print("\n--- Alte sporuri ---")
    other_bonus_value = read_float("Introdu alte sporuri ca sumă fixă (0 dacă nu există): ")
    other_bonus_percent = read_float("Introdu alte sporuri ca procent din brut (0 dacă nu există): ")

    print("\n--- Bonuri ---")
    meal_tickets_value = read_float("Introdu valoarea bonurilor de masă: ")
    cultural_tickets_value = read_float("Introdu valoarea bonurilor culturale: ")

    try:
        results = calc_salary(
            gross_salary=gross_salary,
            total_hours=total_hours,
            night_hours=night_hours,
            weekend_hours=weekend_hours,
            night_bonus_percent=night_bonus_percent,
            weekend_bonus_percent=weekend_bonus_percent,
            other_bonus_value=other_bonus_value,
            other_bonus_percent=other_bonus_percent,
            meal_tickets_value=meal_tickets_value,
            cultural_tickets_value=cultural_tickets_value,
            meal_tickets_tax_percent=19,
            cultural_tickets_tax_percent=10,
        )
        print_results(results)
    except ValueError as error:
        print(f"\nEroare: {error}")


if __name__ == "__main__":
    main()

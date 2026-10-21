# Функция для расчёта, сколько денег приходится на каждый месяц,
# чтобы сумма всех платежей точно совпадала со стоимостью покупки
# (функция для подсчёта рассчрочки)
def create_schedule(amount: int, months: int) -> list[int]:
    result = []

    calculations = amount // months #1990000 // 3 = 663333
    remainder = amount % months #1990000 % 3 = 1

    for i in range(months):
        if i < remainder: #остаток равен 1, значит только первый получит доп. копейку
            result.append(calculations + 1)
        else:
            result.append(calculations)

    return result
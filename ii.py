import random

class AIController:
    def __init__(self, faction):
        self.faction = faction
        self.economy_level = 1
        self.army_strength = 1
        self.diplomacy_status = {}
        self.resources = {
            "money": 1000,
            "people": 500,
        }

    def process_turn(self):
        """Обработка хода ИИ фракции"""
        #print(f"ИИ {self.faction} делает ход...")

        # Экономические действия
        self.manage_economy()

        # Военные действия
        self.manage_army()

        # Дипломатические действия
        self.manage_politics()

    def manage_economy(self):
        """Управление экономикой ИИ"""
        action = random.choice(['build', 'trade', 'expand'])
        if action == 'build':
            self.build_economy()
        elif action == 'trade':
            self.trade_resources()
        elif action == 'expand':
            self.expand_economy()

    def build_economy(self):
        """Построить экономические объекты"""
        if self.resources['money'] >= 200:
            self.economy_level += 1
            self.resources['money'] -= 200
            #print(f"{self.faction} построил экономические здания. Уровень экономики: {self.economy_level}")
        else:
            pass#print(f"{self.faction} не хватает средств для постройки.")

    def trade_resources(self):
        """Торговля ресурсами с другими фракциями"""
        if self.resources['money'] >= 100:
            self.resources['money'] -= 100
            self.resources['people'] += 50
            #print(f"{self.faction} торгует. Деньги: {self.resources['money']}, Люди: {self.resources['people']}")
        else:
            pass#print(f"{self.faction} не хватает денег для торговли.")

    def expand_economy(self):
        """Расширение экономики (например, колонизация или захват территорий)"""
        if self.resources['people'] >= 100:
            self.resources['people'] -= 100
            self.economy_level += 0.5
            #print(f"{self.faction} расширяет экономику. Новый уровень экономики: {self.economy_level}")
        else:
            pass#print(f"{self.faction} не хватает людей для расширения экономики.")

    def manage_army(self):
        """Управление армией ИИ"""
        action = random.choice(['train', 'attack', 'defend'])
        if action == 'train':
            self.train_army()
        elif action == 'attack':
            self.attack_enemy()
        elif action == 'defend':
            self.defend_territory()

    def train_army(self):
        """Тренировка войск"""
        if self.resources['money'] >= 150:
            self.army_strength += 1
            self.resources['money'] -= 150
            #print(f"{self.faction} тренирует войска. Сила армии: {self.army_strength}")
        else:
            pass#print(f"{self.faction} не хватает средств для тренировки армии.")

    def attack_enemy(self):
        """Атака на соседнюю фракцию"""
        if self.army_strength > 2:
            target = random.choice(list(self.diplomacy_status.keys()))
            print(f"{self.faction} атакует {target}.")
            # Логика успеха атаки
            success = random.random() < 0.5
            if success:
                pass#print(f"Атака {self.faction} на {target} была успешной!")
            else:
               pass #print(f"Атака {self.faction} на {target} провалилась.")
        else:
           pass #print(f"{self.faction} армия слишком слаба для атаки.")

    def defend_territory(self):
        """Защита территории"""
        #print(f"{self.faction} готовится к защите.")

    def manage_politics(self):
        """Управление дипломатией ИИ"""
        if len(self.diplomacy_status) > 0:
            target = random.choice(list(self.diplomacy_status.keys()))
            action = random.choice(['ally', 'negotiate', 'betray'])
            if action == 'ally':
                self.form_alliance(target)
            elif action == 'negotiate':
                self.negotiate_peace(target)
            elif action == 'betray':
                self.betray_ally(target)

    def form_alliance(self, target):
        """Создание альянса"""
        pass

    def negotiate_peace(self, target):
        """Переговоры о мире"""
        pass

    def betray_ally(self, target):
        """Предательство альянса"""
        pass

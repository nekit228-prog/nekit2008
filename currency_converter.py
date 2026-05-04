import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import requests
import os

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter - Конвертер валют")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        
        # Данные
        self.api_key = "YOUR_API_KEY_HERE"  # Замените на ваш API ключ
        self.base_url = "https://v6.exchangerate-api.com/v6/"
        self.currencies = []
        self.history_file = "conversion_history.json"
        self.history = []
        
        # Популярные валюты (на случай, если API недоступен)
        self.common_currencies = {
            "USD": "Доллар США",
            "EUR": "Евро",
            "RUB": "Российский рубль",
            "GBP": "Британский фунт",
            "JPY": "Японская иена",
            "CNY": "Китайский юань",
            "CAD": "Канадский доллар",
            "CHF": "Швейцарский франк",
            "AUD": "Австралийский доллар",
            "TRY": "Турецкая лира"
        }
        
        # Загрузка истории
        self.load_history()
        
        # Получение списка валют
        self.get_currency_list()
        
        # Создание интерфейса
        self.create_widgets()
        self.update_history_display()
    
    def get_currency_list(self):
        """Получение списка доступных валют из API"""
        try:
            url = f"{self.base_url}{self.api_key}/codes"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data["result"] == "success":
                    self.currencies = [code for code, name in data["supported_codes"]]
                    return
        except Exception as e:
            print(f"Не удалось загрузить список валют: {e}")
        
        # Если API не доступен, используем стандартный список
        self.currencies = list(self.common_currencies.keys())
        messagebox.showwarning("Предупреждение", 
                              "Не удалось загрузить список валют из API.\n"
                              "Используется стандартный список валют.")
    
    def get_currency_name(self, code):
        """Получение названия валюты"""
        return self.common_currencies.get(code, code)
    
    def create_widgets(self):
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка веса
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # ===== Панель конвертации =====
        convert_frame = ttk.LabelFrame(main_frame, text="Конвертация валют", padding="10")
        convert_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        convert_frame.columnconfigure(1, weight=1)
        convert_frame.columnconfigure(3, weight=1)
        
        # Из валюты
        ttk.Label(convert_frame, text="Из валюты:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.from_currency = ttk.Combobox(convert_frame, values=self.currencies, width=10)
        self.from_currency.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.from_currency.set("USD")
        
        # Сумма
        ttk.Label(convert_frame, text="Сумма:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.amount_entry = ttk.Entry(convert_frame, width=15)
        self.amount_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # В валюту
        ttk.Label(convert_frame, text="В валюту:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.to_currency = ttk.Combobox(convert_frame, values=self.currencies, width=10)
        self.to_currency.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.to_currency.set("EUR")
        
        # Результат
        ttk.Label(convert_frame, text="Результат:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.result_label = ttk.Label(convert_frame, text="0.00", font=("Arial", 12, "bold"))
        self.result_label.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Кнопка конвертации
        ttk.Button(convert_frame, text="🔄 Конвертировать", command=self.convert_currency).grid(row=2, column=0, columnspan=4, pady=10)
        
        # Кнопка обновления курсов
        ttk.Button(convert_frame, text="📡 Обновить курсы", command=self.update_rates).grid(row=3, column=0, columnspan=2, pady=5)
        
        # Кнопка сброса
        ttk.Button(convert_frame, text="🗑 Очистить", command=self.clear_fields).grid(row=3, column=2, columnspan=2, pady=5)
        
        # ===== Информация о курсе =====
        self.rate_info_label = ttk.Label(main_frame, text="", foreground="blue")
        self.rate_info_label.grid(row=1, column=0, pady=(0, 10))
        
        # ===== Панель управления историей =====
        history_control_frame = ttk.Frame(main_frame)
        history_control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(history_control_frame, text="💾 Сохранить историю", command=self.save_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(history_control_frame, text="📂 Загрузить историю", command=self.load_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(history_control_frame, text="🗑 Очистить историю", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        
        # ===== Таблица истории =====
        history_frame = ttk.LabelFrame(main_frame, text="История конвертаций", padding="10")
        history_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # Создание таблицы
        columns = ("date", "from_amount", "from_currency", "to_amount", "to_currency", "rate")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=10)
        
        # Настройка заголовков
        self.tree.heading("date", text="Дата и время")
        self.tree.heading("from_amount", text="Сумма")
        self.tree.heading("from_currency", text="Из")
        self.tree.heading("to_amount", text="Результат")
        self.tree.heading("to_currency", text="В")
        self.tree.heading("rate", text="Курс")
        
        # Настройка ширины колонок
        self.tree.column("date", width=150)
        self.tree.column("from_amount", width=100)
        self.tree.column("from_currency", width=80)
        self.tree.column("to_amount", width=100)
        self.tree.column("to_currency", width=80)
        self.tree.column("rate", width=100)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Статусная строка
        self.status_label = ttk.Label(main_frame, text="Готово", relief=tk.SUNKEN)
        self.status_label.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def validate_amount(self, amount_str):
        """Проверка корректности суммы"""
        try:
            amount = float(amount_str)
            if amount <= 0:
                return False, "Сумма должна быть положительным числом"
            return True, amount
        except ValueError:
            return False, "Введите корректное число"
    
    def get_exchange_rate(self, from_currency, to_currency):
        """Получение курса обмена из API"""
        try:
            url = f"{self.base_url}{self.api_key}/pair/{from_currency}/{to_currency}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data["result"] == "success":
                    rate = data["conversion_rate"]
                    return True, rate
                else:
                    return False, "Ошибка API"
            else:
                return False, f"HTTP ошибка: {response.status_code}"
        except requests.exceptions.Timeout:
            return False, "Превышено время ожидания"
        except requests.exceptions.ConnectionError:
            return False, "Ошибка подключения к интернету"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def convert_currency(self):
        """Конвертация валюты"""
        # Получение данных
        from_curr = self.from_currency.get().strip().upper()
        to_curr = self.to_currency.get().strip().upper()
        amount_str = self.amount_entry.get().strip()
        
        # Проверка суммы
        is_valid, result = self.validate_amount(amount_str)
        if not is_valid:
            messagebox.showerror("Ошибка", result)
            return
        
        amount = result
        
        # Проверка выбора валют
        if not from_curr or not to_curr:
            messagebox.showerror("Ошибка", "Выберите валюты для конвертации")
            return
        
        if from_curr == to_curr:
            converted_amount = amount
            rate = 1.0
            self.result_label.config(text=f"{converted_amount:.2f}")
            self.rate_info_label.config(text=f"Курс: 1 {from_curr} = 1 {to_curr}")
            self.add_to_history(from_curr, to_curr, amount, converted_amount, rate)
            return
        
        # Получение курса из API
        success, rate_or_error = self.get_exchange_rate(from_curr, to_curr)
        
        if not success:
            messagebox.showerror("Ошибка", f"Не удалось получить курс:\n{rate_or_error}")
            return
        
        rate = rate_or_error
        converted_amount = amount * rate
        
        # Обновление интерфейса
        self.result_label.config(text=f"{converted_amount:.2f}")
        self.rate_info_label.config(text=f"Курс: 1 {from_curr} = {rate:.4f} {to_curr}")
        
        # Добавление в историю
        self.add_to_history(from_curr, to_curr, amount, converted_amount, rate)
        
        self.update_status(f"Конвертировано: {amount} {from_curr} = {converted_amount:.2f} {to_curr}")
    
    def add_to_history(self, from_curr, to_curr, amount, converted_amount, rate):
        """Добавление записи в историю"""
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from_amount": amount,
            "from_currency": from_curr,
            "to_amount": round(converted_amount, 2),
            "to_currency": to_curr,
            "rate": round(rate, 4)
        }
        
        self.history.append(entry)
        self.update_history_display()
        self.save_history()
    
    def update_history_display(self):
        """Обновление таблицы истории"""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Добавление записей в обратном порядке (новые сверху)
        for entry in reversed(self.history):
            self.tree.insert("", "end", values=(
                entry["date"],
                f"{entry['from_amount']:.2f}",
                entry["from_currency"],
                f"{entry['to_amount']:.2f}",
                entry["to_currency"],
                f"{entry['rate']:.4f}"
            ))
        
        # Обновление статуса
        self.update_status(f"Всего операций в истории: {len(self.history)}")
    
    def save_history(self):
        """Сохранение истории в JSON файл"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
            self.update_status(f"История сохранена в {self.history_file}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю:\n{str(e)}")
    
    def load_history(self):
        """Загрузка истории из JSON файла"""
        if not os.path.exists(self.history_file):
            messagebox.showwarning("Предупреждение", f"Файл {self.history_file} не найден")
            return
        
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                self.history = json.load(f)
            self.update_history_display()
            messagebox.showinfo("Успех", f"Загружено {len(self.history)} записей из истории")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить историю:\n{str(e)}")
    
    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю?"):
            self.history = []
            self.update_history_display()
            self.save_history()
            self.update_status("История очищена")
    
    def update_rates(self):
        """Обновление курсов валют"""
        from_curr = self.from_currency.get().strip().upper()
        to_curr = self.to_currency.get().strip().upper()
        
        if not from_curr or not to_curr:
            messagebox.showwarning("Предупреждение", "Выберите валюты для проверки курса")
            return
        
        success, rate_or_error = self.get_exchange_rate(from_curr, to_curr)
        
        if success:
            self.rate_info_label.config(text=f"Актуальный курс: 1 {from_curr} = {rate_or_error:.4f} {to_curr}")
            self.update_status(f"Курс обновлен: {from_curr}/{to_curr} = {rate_or_error:.4f}")
            messagebox.showinfo("Курс обновлен", f"1 {from_curr} = {rate_or_error:.4f} {to_curr}")
        else:
            messagebox.showerror("Ошибка", f"Не удалось получить курс:\n{rate_or_error}")
    
    def clear_fields(self):
        """Очистка полей ввода"""
        self.amount_entry.delete(0, tk.END)
        self.result_label.config(text="0.00")
        self.rate_info_label.config(text="")
        self.update_status("Поля очищены")
    
    def update_status(self, message):
        """Обновление статусной строки"""
        self.status_label.config(text=message)

def main():
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    
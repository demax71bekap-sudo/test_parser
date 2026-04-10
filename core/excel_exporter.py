import pandas as pd
import os
from typing import List
from core.product_model import Product
from utils.logger import get_logger

logger = get_logger(__name__)


def export_to_excel(products: List[Product], output_path: str) -> bool:
    """
    Экспорт списка товаров в Excel
    - Динамические колонки для характеристик
    - Фиксированные колонки: Артикул, Название, Цена, Описание, Изображение
    """
    try:
        if not products:
            logger.warning("Список товаров пуст")
            return False

        # Создание директории
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Сбор всех уникальных ключей характеристик
        all_specs_keys = set()
        for p in products:
            if p.specs:
                all_specs_keys.update(p.specs.keys())

        # Фиксированные колонки
        fixed_columns = ["Артикул", "Название", "Цена", "Категория", "Описание", "Изображение", "URL"]

        # Динамические колонки (характеристики)
        spec_columns = sorted(all_specs_keys)

        # Все колонки
        all_columns = fixed_columns + spec_columns

        # Подготовка данных
        rows = []
        for p in products:
            row = {
                "Артикул": p.article,
                "Название": p.name,
                "Цена": p.price,
                "Категория": p.category,
                "Описание": p.description[:32000] if p.description else "",  # Ограничение Excel
                "Изображение": p.image_path,
                "URL": p.detail_url
            }

            # Добавление характеристик
            if p.specs:
                for key, value in p.specs.items():
                    row[key] = value

            rows.append(row)

        # Создание DataFrame
        df = pd.DataFrame(rows, columns=all_columns)

        # Экспорт в Excel
        df.to_excel(output_path, index=False, sheet_name="Товары")

        logger.info(f"Экспорт завершён: {output_path} ({len(products)} товаров)")
        return True

    except Exception as e:
        logger.error(f"Ошибка экспорта в Excel: {e}")
        return False
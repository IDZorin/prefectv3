#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import shutil
import sys

VALID_MODES = {"delete", "create", "delete_create"}

def load_or_create_config(config_path: Path) -> dict:
    if not config_path.exists():
        default = "mode=delete_create\ncount=3\nsource_dir=index\n"
        config_path.write_text(default, encoding="utf-8")
        print('Создан файл "config.txt" с настройками по умолчанию.')
    cfg = {}
    for line in config_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            print(f'Предупреждение: пропущена строка в config.txt: "{line}"')
            continue
        k, v = line.split("=", 1)
        cfg[k.strip().lower()] = v.strip()
    return cfg

def validate_config(cfg: dict) -> tuple[str, int, str]:
    mode = cfg.get("mode", "delete_create").lower()
    if mode not in VALID_MODES:
        raise ValueError(f'Недопустимый mode="{mode}". Допустимо: {", ".join(sorted(VALID_MODES))}.')
    try:
        count = int(cfg.get("count", "3"))
    except ValueError:
        raise ValueError(f'count должен быть целым числом, получено "{cfg.get("count")}".')
    if count < 1:
        raise ValueError("count должен быть >= 1.")
    source_dir = cfg.get("source_dir", "index").strip()
    if not source_dir:
        raise ValueError("source_dir не может быть пустым.")
    return mode, count, source_dir

def ensure_is_dir(path: Path):
    if path.exists() and path.is_file():
        path.unlink()

def delete_targets(targets: list[Path]):
    for t in targets:
        if t.exists():
            if t.is_dir():
                print(f'Удаляю "{t.name}"...')
                shutil.rmtree(t)
            else:
                print(f'Удаляю файл "{t.name}"...')
                t.unlink()
        else:
            print(f'"{t.name}" не найдено - пропускаю.')

def create_targets(src: Path, targets: list[Path]):
    if not src.exists() or not src.is_dir():
        raise FileNotFoundError(f'Исходная папка "{src.name}" не найдена.')
    for t in targets:
        if t.exists():
            if t.is_dir():
                print(f'"{t.name}" уже существует - удаляю перед копированием...')
                shutil.rmtree(t)
            else:
                print(f'Файл "{t.name}" мешает - удаляю...')
                t.unlink()
        print(f'Копирую "{src.name}" -> "{t.name}"...')
        shutil.copytree(src, t)

def main():
    base_dir = Path(__file__).resolve().parent
    config_path = base_dir / "config.txt"

    cfg = load_or_create_config(config_path)
    try:
        mode, count, source_dir_name = validate_config(cfg)
    except Exception as e:
        print(f"Ошибка в config.txt: {e}")
        sys.exit(2)

    src_dir = base_dir / source_dir_name
    targets = [base_dir / f"{source_dir_name}{i}" for i in range(1, count + 1)]

    for t in targets:
        ensure_is_dir(t)

    print(f"Режим: {mode}, копий: {count}, исходная папка: {source_dir_name}")

    try:
        if mode == "delete":
            delete_targets(targets)
        elif mode == "create":
            create_targets(src_dir, targets)
        elif mode == "delete_create":
            delete_targets(targets)
            create_targets(src_dir, targets)
        print("Готово.")
    except Exception as e:
        print(f"Ошибка выполнения: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

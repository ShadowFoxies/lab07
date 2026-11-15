import time
from typing import Any


def balance_server_pool(*servers: tuple, **options: Any) -> dict[str, Any]:
	"""
	Приймає записи про сервери через *args та параметри фільтрації через **kwargs.
	Формат одного запису: (server_id, load_pct, ping_ms, is_online).
	"""
	# Дефолтні пороги, якщо при виклику їх не передали в options
	max_load = options.get("max_load", 85.0)
	max_ping = options.get("max_ping", 150.0)
	only_online = options.get("only_online", True)

	accepted = []

	for idx, item in enumerate(servers, start=1):
		# Перевірка формату кортежу
		if not isinstance(item, tuple) or len(item) != 4:
			print(f"[Увага] Запис #{idx} пропущено: очікується кортеж із 4 полів.")
			continue

		srv_id, load_pct, ping_ms, is_online = item

		# Перевірка типів (bool у Python є підкласом int, тому відсікаємо його окремо)
		valid_id = isinstance(srv_id, str) and len(srv_id.strip()) > 0
		valid_load = isinstance(load_pct, (int, float)) and not isinstance(load_pct, bool)
		valid_ping = isinstance(ping_ms, (int, float)) and not isinstance(ping_ms, bool)
		valid_status = isinstance(is_online, bool)

		if not (valid_id and valid_load and valid_ping and valid_status):
			print(f"[Помилка] Запис #{idx} ({srv_id}): некоректні типи даних.")
			continue

		# Фізичні обмеження параметрів
		if not (0.0 <= load_pct <= 100.0) or ping_ms < 0:
			print(f"[Помилка] Запис #{idx} ({srv_id}): значення поза допустимими межами.")
			continue

		# Відбір за умовами балансування з **kwargs
		if only_online and not is_online:
			continue
		if load_pct > max_load or ping_ms > max_ping:
			continue

		accepted.append({
			"server_id": srv_id.strip(),
			"load_pct": float(load_pct),
			"ping_ms": float(ping_ms),
			"is_online": is_online,
		})

	# Агрегація середніх показників по пулу
	if accepted:
		avg_load = sum(s["load_pct"] for s in accepted) / len(accepted)
		avg_ping = sum(s["ping_ms"] for s in accepted) / len(accepted)
	else:
		avg_load = 0.0
		avg_ping = 0.0

	return {
		"servers": accepted,
		"total_received": len(servers),
		"accepted_count": len(accepted),
		"rejected_count": len(servers) - len(accepted),
		"avg_load": round(avg_load, 2),
		"avg_ping": round(avg_ping, 2),
	}


def main() -> None:
	print("=" * 76)
	print(f"{'МОДУЛЬ БАЛАНСУВАННЯ НАВАНТАЖЕННЯ (ВАРІАНТ 18)':^76}")
	print("=" * 76)

	# Тестовий набір серверів (однакові Load % на EU-02 та US-01 для перевірки 2-го критерію)
	raw_servers = (
		("EU-NODE-01", 54.2, 28.5, True),
		("EU-NODE-02", 32.0, 41.0, True),
		("US-NODE-01", 32.0, 19.4, True),
		("AS-NODE-04", 91.5, 65.0, True),    # не пройде за max_load
		("EU-NODE-03", 18.0, 210.0, True),   # не пройде за max_ping
		("BACKUP-01", 12.0, 15.0, False),    # офлайн
		("BAD-NODE", 120.0, 10.0, True),     # некоректне навантаження (>100%)
		("EU-NODE-05", 45.8, 33.2, True),
	)

	pool_data = balance_server_pool(
		*raw_servers,
		max_load=85.0,
		max_ping=150.0,
		only_online=True,
	)

	print(
		f"\nОтримано записів: {pool_data['total_received']} | "
		f"Доступних для балансування: {pool_data['accepted_count']} | "
		f"Відхилено: {pool_data['rejected_count']}"
	)
	print(
		f"Середнє навантаження: {pool_data['avg_load']}% | "
		f"Середній пінг: {pool_data['avg_ping']} мс\n"
	)

	# Сортування за зростанням Load %, а при збігу — за зростанням Ping_MS
	sorted_servers = sorted(
		pool_data["servers"],
		key=lambda srv: (srv["load_pct"], srv["ping_ms"]),
	)

	print(f"| {'№':^4} | {'Сервер':^16} | {'Load (%)':^12} | {'Ping (мс)':^12} | {'Статус':^10} |")
	print("-" * 70)
	for i, srv in enumerate(sorted_servers, start=1):
		status_str = "ONLINE" if srv["is_online"] else "OFFLINE"
		print(
			f"| {i:^4} | {srv['server_id']:<16} | {srv['load_pct']:^12.1f} | "
			f"{srv['ping_ms']:^12.1f} | {status_str:^10} |"
		)
	print("=" * 70)


if __name__ == "__main__":
	t_start = time.perf_counter()
	main()
	t_elapsed = (time.perf_counter() - t_start) * 1000
	print(f"\nЧас виконання модуля: {t_elapsed:.3f} мс")

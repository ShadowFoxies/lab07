import sys
import time


class RecursionDepthTracker:
	"""Відстежує поточну та максимальну глибину стека і блокує переповнення."""

	def __init__(self, max_allowed_depth: int = 300):
		self.current_depth = 0
		self.max_observed_depth = 0
		self.max_allowed_depth = max_allowed_depth

	def enter(self) -> None:
		self.current_depth += 1
		if self.current_depth > self.max_observed_depth:
			self.max_observed_depth = self.current_depth
		if self.current_depth > self.max_allowed_depth:
			raise RecursionError(
				f"Перевищено допустиму глибину рекурсії: {self.current_depth} > {self.max_allowed_depth}"
			)

	def leave(self) -> None:
		self.current_depth -= 1


def levenshtein_recursive(s1: str, s2: str, tracker: RecursionDepthTracker) -> int:
	"""Рекурсивний розрахунок відстані Левенштейна з контролем глибини викликів."""

	def _dist(i: int, j: int) -> int:
		# s1, s2 та tracker беруться із зовнішньої області видимості (правило LEGB)
		tracker.enter()
		try:
			if i == 0:
				return j
			if j == 0:
				return i

			if s1[i - 1] == s2[j - 1]:
				return _dist(i - 1, j - 1)

			delete_op = _dist(i - 1, j)
			insert_op = _dist(i, j - 1)
			replace_op = _dist(i - 1, j - 1)
			return 1 + min(delete_op, insert_op, replace_op)
		finally:
			# Зменшуємо лічильник навіть якщо спрацював виняток RecursionError
			tracker.leave()

	return _dist(len(s1), len(s2))


def levenshtein_iterative(s1: str, s2: str) -> int:
	"""Ітеративний алгоритм Вагнера — Фішера (динамічне програмування)."""
	m, n = len(s1), len(s2)
	if m == 0:
		return n
	if n == 0:
		return m

	prev_row = list(range(n + 1))
	for i in range(1, m + 1):
		curr_row = [i] + [0] * n
		for j in range(1, n + 1):
			cost = 0 if s1[i - 1] == s2[j - 1] else 1
			curr_row[j] = min(
				prev_row[j] + 1,        # видалення символу
				curr_row[j - 1] + 1,    # вставка символу
				prev_row[j - 1] + cost  # заміна символу
			)
		prev_row = curr_row

	return prev_row[n]


def main() -> None:
	print("=" * 76)
	print(f"{'ОБЧИСЛЕННЯ ВІДСТАНІ ЛЕВЕНШТЕЙНА (ВАРІАНТ 18)':^76}")
	print("=" * 76)

	sys_limit = sys.getrecursionlimit()
	print(f"Системний ліміт рекурсії CPython: {sys_limit} кадрів\n")

	test_pairs = [
		("kitten", "sitting"),
		("saturday", "sunday"),
		("execution", "intention"),
		("algorithm", "altruism"),
	]

	for str_a, str_b in test_pairs:
		tracker = RecursionDepthTracker(max_allowed_depth=min(200, sys_limit - 50))

		t0 = time.perf_counter()
		dist_rec = levenshtein_recursive(str_a, str_b, tracker)
		time_rec_ms = (time.perf_counter() - t0) * 1000

		t1 = time.perf_counter()
		dist_iter = levenshtein_iterative(str_a, str_b)
		time_iter_ms = (time.perf_counter() - t1) * 1000

		match = dist_rec == dist_iter
		speedup = time_rec_ms / time_iter_ms if time_iter_ms > 0 else 0.0

		print(f"Рядки: '{str_a}' <-> '{str_b}'")
		print(f"  Відстань (рекурсія / ітерація): {dist_rec} / {dist_iter} (збіг: {match})")
		print(f"  Макс. глибина стека:            {tracker.max_observed_depth} кадрів")
		print(f"  Час (рекурсія vs ітерація):     {time_rec_ms:.4f} мс vs {time_iter_ms:.4f} мс (у {speedup:.1f}x повільніше)")
		print("-" * 76)

	# Перевірка спрацювання захисту при перевищенні допустимої глибини
	print("\nТест захисту від переповнення стека (ліміт = 15 кадрів):")
	guard_tracker = RecursionDepthTracker(max_allowed_depth=15)
	long_a = "computer_engineering"
	long_b = "software_development"
	try:
		levenshtein_recursive(long_a, long_b, guard_tracker)
	except RecursionError as err:
		print(f"  [Захист спрацював] {err}")
		# Ітеративний метод при цьому спокійно обчислює результат без навантаження на стек
		safe_dist = levenshtein_iterative(long_a, long_b)
		print(f"  Ітеративний аналог порахував без помилки: відстань = {safe_dist}")
	print("=" * 76)


if __name__ == "__main__":
	main()

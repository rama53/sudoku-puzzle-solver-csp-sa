import random
import math
import time
from copy import deepcopy

class PuzzleGenerator:
    def is_valid(self, board, row, col, num):
        for i in range(9):
            if board[row][i] == num or board[i][col] == num:
                return False

        box_row_start = row - row % 3
        box_col_start = col - col % 3
        for i in range(3):
            for j in range(3):
                if board[i + box_row_start][j + box_col_start] == num:
                    return False
        return True

    def fill_grid(self, grid):
        for i in range(9):
            for j in range(9):
                if grid[i][j] == 0:
                    nums = list(range(1, 10))
                    random.shuffle(nums)
                    for num in nums:
                        if self.is_valid(grid, i, j, num):
                            grid[i][j] = num
                            if self.fill_grid(grid):
                                return True
                            grid[i][j] = 0
                    return False
        return True

    def generate_sudoku(self, min_clues=30):
        grid = [[0] * 9 for _ in range(9)]
        self.fill_grid(grid)

        puzzle = [row[:] for row in grid]
        cells_to_remove = 81 - min_clues
        all_cells = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(all_cells)

        for i in range(cells_to_remove):
            r, c = all_cells[i]
            puzzle[r][c] = 0

        return puzzle, grid

def print_clear(grid):
    for r in range(9):
        if r in (3,6):
            print("-" * 21)  
        row = ""
        for c in range(9):
            if c in (3,6):
                row += "| "
            row += str(grid[r][c]) + " "
        print(row)


# Simulated Annealing
def fix_sudoku_values(grid):
    fixed = [[0] * 9 for _ in range(9)]
    for r in range(9):
        for c in range(9):
            if grid[r][c] != 0:
                fixed[r][c] = 1
    return fixed


def row_col_errors(grid):
    errors = 0
    for i in range(9):
        errors += 9 - len(set(grid[i]))
        col = [grid[r][i] for r in range(9)]
        errors += 9 - len(set(col))
    return errors


def create_blocks():
    return [[[br * 3 + r, bc * 3 + c]
             for r in range(3) for c in range(3)]
            for br in range(3) for bc in range(3)]


def fill_blocks_random(grid, blocks):
    for block in blocks:
        used = [grid[r][c] for r, c in block if grid[r][c] != 0]
        available = [v for v in range(1, 10) if v not in used]
        random.shuffle(available)
        k = 0
        for r, c in block:
            if grid[r][c] == 0:
                grid[r][c] = available[k]
                k += 1
    return grid


def solve_sudoku_sa(grid, sigma_init, cooling_rate, max_iterations=10000):
    fixed = fix_sudoku_values(grid)
    blocks = create_blocks()
    current = fill_blocks_random([row[:] for row in grid], blocks)
    score = row_col_errors(current)
    temperature = sigma_init
    iterations = 0

    for _ in range(max_iterations):
        iterations += 1
        if score == 0:
            break

        block = random.choice(blocks)
        non_fixed = [c for c in block if fixed[c[0]][c[1]] == 0]

        if len(non_fixed) >= 2:
            a, b = random.sample(non_fixed, 2)
            new_grid = [row[:] for row in current]
            new_grid[a[0]][a[1]], new_grid[b[0]][b[1]] = \
                new_grid[b[0]][b[1]], new_grid[a[0]][a[1]]

            new_score = row_col_errors(new_grid)
            diff = new_score - score

            if diff <= 0 or random.random() < math.exp(-diff / temperature):
                current = new_grid
                score = new_score

        temperature *= cooling_rate

    return current, score, iterations


def is_valid_sudoku(grid):
    for i in range(9):
        if len(set(grid[i])) != 9:
            return False
        col = [grid[r][i] for r in range(9)]
        if len(set(col)) != 9:
            return False

    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            block = [grid[r][c] for r in range(br, br + 3)
                                   for c in range(bc, bc + 3)]
            if len(set(block)) != 9:
                return False
    return True


# CSP Solver
class CSPSolver:
    def __init__(self, puzzle):
        self.puzzle = puzzle
        self.cells = self._initialize_cells()
        self.nodes_explored = 0

    def _initialize_cells(self):
        cells = []
        for i in range(9):
            for j in range(9):
                val = self.puzzle.grid[i][j]
                cells.append({
                    "row": i,
                    "col": j,
                    "value": val,
                    "domain": [val] if val != 0 else self._get_domain(i, j)
                })
        return cells

    def _get_domain(self, row, col):
        possible = set(range(1, 10))
        for c in range(9):
            possible.discard(self.puzzle.grid[row][c])
        for r in range(9):
            possible.discard(self.puzzle.grid[r][col])
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                possible.discard(self.puzzle.grid[br + i][bc + j])
        return list(possible)

    def _select_mrv(self):
        unassigned = [c for c in self.cells if c["value"] == 0]
        return min(unassigned, key=lambda c: len(c["domain"])) if unassigned else None

    def _order_lcv(self, cell):
        values = []
        for v in cell["domain"]:
            count = 0
            for n in self.cells:
                if n["value"] == 0 and n is not cell:
                    if (n["row"] == cell["row"] or
                        n["col"] == cell["col"] or
                        (n["row"] // 3 == cell["row"] // 3 and
                         n["col"] // 3 == cell["col"] // 3)):
                        if v in n["domain"]:
                            count += 1
            values.append((count, v))
        values.sort()
        return [v for _, v in values]

    def _forward_check(self, cell, value):
        saved = {i: c["domain"][:] for i, c in enumerate(self.cells)}
        for n in self.cells:
            if n["value"] == 0 and n is not cell:
                if (n["row"] == cell["row"] or
                    n["col"] == cell["col"] or
                    (n["row"] // 3 == cell["row"] // 3 and
                     n["col"] // 3 == cell["col"] // 3)):
                    if value in n["domain"]:
                        n["domain"].remove(value)
                    if not n["domain"]:
                        return None
        return saved

    def _restore_domains(self, saved):
        for i, dom in saved.items():
            self.cells[i]["domain"] = dom

    def _backtrack(self):
        self.nodes_explored += 1
        cell = self._select_mrv()
        if cell is None:
            return True

        for value in self._order_lcv(cell):
            cell["value"] = value
            saved = self._forward_check(cell, value)
            if saved is not None and self._backtrack():
                return True
            cell["value"] = 0
            if saved:
                self._restore_domains(saved)
        return False

    def solve_CSP(self):
        start = time.time()
        success = self._backtrack()
        duration = time.time() - start
        if success:
            for c in self.cells:
                self.puzzle.grid[c["row"]][c["col"]] = c["value"]
        return success, duration

def choose_difficulty():
    print("\nChoose difficulty level:")
    print(" 1. Easy (36 clues)")
    print(" 2. Medium (32 clues)")
    print(" 3. Hard (28 clues)")
    d = input("\nYour choice (1-3): ").strip()
    clues = {1: 36, 2: 32}.get(int(d) if d.isdigit() else 0, 28)
    return clues, {36: "Easy", 32: "Medium", 28: "Hard"}[clues]

def run_sa(puzzle):
    sigma = float(input("\nInitial temperature: "))
    alpha = float(input("Cooling rate: "))

    start = time.time()
    sol, err, it = solve_sudoku_sa([row[:] for row in puzzle], sigma, alpha)
    runtime = time.time() - start

    valid = is_valid_sudoku(sol)

    print("\n--- Simulated Annealing Result ---")
    print_clear(sol)
    print("Solution validity (True/False):", valid)
    print("Number of violations:", err)
    print(f"Runtime: {runtime:.3f}s")
    print("Iterations until convergence:", it)

def run_csp(puzzle):
    obj = type("Puzzle", (), {"grid": [row[:] for row in puzzle]})()
    solver = CSPSolver(obj)

    success, t = solver.solve_CSP()

    valid = is_valid_sudoku(obj.grid) if success else False
    violations = 0 if valid else row_col_errors(obj.grid)
    iterations = solver.nodes_explored
    runtime = t

    print("\n--- CSP Result ---")
    if success:
        print_clear(obj.grid)
    else:
        print("No solution found")

    print("Solution validity (True/False):", valid)
    print("Number of violations:", violations)
    print(f"Runtime: {runtime:.3f}s")
    print("Iterations until convergence:", iterations)



# Main Program
def main():
    print("\n---- SUDOKU GENERATOR & SOLVER ----")
    gen = PuzzleGenerator()
    clues, name = choose_difficulty()
    puzzle, _ = gen.generate_sudoku(clues)
    puzzle = deepcopy(puzzle)

    print(f"\n{name} Sudoku ({clues} clues)")
    print_clear(puzzle)

    while True:
        print("\n1. Run Simulated Annealing")
        print("2. Run CSP")
        print("3. New puzzle")
        print("4. Exit")
        ch = input("Choice: ").strip()

        if ch == "1":
            run_sa(puzzle)
        elif ch == "2":
            run_csp(puzzle)
        elif ch == "3":
            clues, name = choose_difficulty()
            puzzle, _ = gen.generate_sudoku(clues)
            puzzle = deepcopy(puzzle)
            print_clear(puzzle)
        elif ch == "4":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()

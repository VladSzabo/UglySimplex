from pprint import pprint


m = [[1, 1, 1, 1, 0, 0, 30],
     [2, 1, 3, 0, -1, 0, 60],
     [1, -1, 2, 0, 0, 0, 20],
     [-2, -3, -4, 0, 0, 1, 0]
    ]

def get_pivot():
  col = next((i for i in range(len(m[0])) if m[-1][i] == min(m[-1])), None)

  if col is None:
    return None, None
  
  col_values = [m[i][-1] / m[i][col] for i in range(len(m) - 1) if m[i][-1] / m[i][col] > 0]
  row = [i for i in range(len(m) - 1) if m[i][-1] / m[i][col] == min(col_values)][0]
  
  return row, col


def make_one(row, col):
  div = 1 / m[row][col]
  for i in range(len(m[0])):
    m[row][i] *= div


def make_zero(row, col):
  for i in range(len(m)):
    if i != row:
      div = (-1) * m[i][col]
      for j in range(len(m[0])):
        m[i][j] += div * m[row][j]

pprint(m)

while True:
  row, col = get_pivot()

  if row is None:
    break

  print("Pivot: " + str(row) + ", " + str(col))
  make_one(row, col)
  make_zero(row, col)
  print()
  pprint(m)
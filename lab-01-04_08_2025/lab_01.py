def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)

def fibonacci_iterative(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fibonacci_memoization(n, memo=None):
    if memo is None:
        memo = {}
    if n in memo:
        return memo[n]
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    memo[n] = fibonacci_memoization(n - 1, memo) + fibonacci_memoization(n - 2, memo)
    return memo[n]


if __name__ == "__main__":
    n = int(input("Enter the fibonacci number you want: "))
    print("The", n, "th fibonacci number is:", fibonacci(n))
    print("The", n, "th fibonacci number (iterative) is:", fibonacci_iterative(n))
    print("The", n, "th fibonacci number (memoization) is:", fibonacci_memoization(n))
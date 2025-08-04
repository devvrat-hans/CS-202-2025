"""Module for Fibonacci number calculations."""

def fibonacci(num):
    """Return the nth Fibonacci number using recursion."""
    if num <= 0:
        return 0
    if num == 1:
        return 1
    return fibonacci(num - 1) + fibonacci(num - 2)

def fibonacci_iterative(num):
    """Return the nth Fibonacci number using iteration."""
    if num <= 0:
        return 0
    if num == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, num + 1):
        a, b = b, a + b
    return b

def fibonacci_memoization(num, memo=None):
    """Return the nth Fibonacci number using memoization."""
    if memo is None:
        memo = {}
    if num in memo:
        return memo[num]
    if num <= 0:
        return 0
    if num == 1:
        return 1
    memo[num] = fibonacci_memoization(num - 1, memo) + fibonacci_memoization(num - 2, memo)
    return memo[num]

if __name__ == "__main__":
    number = int(input("Enter the fibonacci number you want: "))
    print("The", number, "th fibonacci number is:", fibonacci(number))
    print("The", number, "th fibonacci number (iterative) is:", fibonacci_iterative(number))
    print("The", number, "th fibonacci number (memoization) is:", fibonacci_memoization(number))

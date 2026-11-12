# Study recommendation

**Your question:** I want to study Python decorators. What should I review first?

## Recommended topic: Python Decorators

**Why it is relevant:** A decorator is a function that wraps another function to add behavior to it without changing its code.

## Prerequisites to review first
- Functions
- Scope
- First-class functions

## Key concepts
- Higher-order functions
- Wrapper functions
- The @ syntax
- functools.wraps

## Practice idea
Create a decorator that logs the name of a function each time it is called.

## Common mistakes to avoid
- Forgetting to return the wrapper function
- Forgetting to pass *args and **kwargs to the original function
- Losing the original function name and docstring by not using functools.wraps

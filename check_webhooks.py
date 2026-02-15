import ast

with open('app/api/endpoints/webhooks.py', 'r') as f:
    code = f.read()

tree = ast.parse(code)

# Find all top-level assignments
print("Top-level assignments:")
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                print(f"  {target.id} at line {node.lineno}")

print("\nTop-level functions:")
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        print(f"  {node.name} at line {node.lineno}")

print("\nTop-level decorators:")
for node in tree.body:
    if hasattr(node, 'decorator_list'):
        if node.decorator_list:
            print(f"  {node.name if hasattr(node, 'name') else 'unknown'} has {len(node.decorator_list)} decorators")

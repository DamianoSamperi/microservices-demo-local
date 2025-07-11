import re

input_file = "products.sql"
output_file = "products_fixed.sql"
vector_dim = 384

# Matcha stringhe tipo '[...numeri...]' tra virgolette
pattern = re.compile(r"'(\[\s*[-\d.,\s\n]+?\s*\])'")

def fix_vector_string(match):
    raw = match.group(1)
    # Unisci tutto in una riga
    cleaned = raw.replace("\n", " ").replace("\r", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Rimuovi [] e splitta
    numbers = cleaned.strip("[]").split(",")

    # Ripulisci ogni numero
    numbers = [n.strip() for n in numbers if n.strip()]

    # Pad o taglia
    if len(numbers) < vector_dim:
        numbers += ["0"] * (vector_dim - len(numbers))
    elif len(numbers) > vector_dim:
        numbers = numbers[:vector_dim]

    return f"ARRAY[{', '.join(numbers)}]::vector({vector_dim})"

# Carica SQL, sostituisci, salva
with open(input_file, "r") as f:
    sql = f.read()

fixed_sql = pattern.sub(fix_vector_string, sql)

with open(output_file, "w") as f:
    f.write(fixed_sql)

print("✅ File corretto salvato in products_fixed.sql")

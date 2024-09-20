import math

def round_to_first_three_nonzero_digits(number):
    # Handle the case when number is 0
  try:
    number = float(number)
    if number == 0:
        return 0

    # Get the scientific notation of the number
    sci_notation = f"{number:.3e}"
    base, exponent = sci_notation.split('e')
    exponent = int(exponent)

    # Round to three significant figures
    rounded_number = round(number, -exponent + 2)
      
    return rounded_number
  except ValueError as e:
    print(f"Error rounding number: {e}")
    return None
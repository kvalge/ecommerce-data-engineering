import requests


def extract_products():
    url = "https://fakestoreapi.com/products"

    response = requests.get(url)

    response.raise_for_status()
    
    return response.json()


if __name__ == "__main__":
    products = extract_products()
    print(products[:2])
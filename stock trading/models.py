from django.db import models
from django.contrib.auth.models import User

class Stock(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.symbol})"

class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    average_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol}"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} {self.quantity} {self.stock.symbol} at {self.price}"

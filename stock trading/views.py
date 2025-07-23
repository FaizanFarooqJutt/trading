from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from decimal import Decimal
from .models import Stock, Portfolio, Transaction
import yfinance as yf
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

def home(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already exists'})
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('dashboard')
    return render(request, 'signup.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    query = request.GET.get('q', '')
    if query:
        stocks = Stock.objects.filter(Q(name__icontains=query) | Q(symbol__icontains=query))
    else:
        stocks = Stock.objects.all()

    portfolio = Portfolio.objects.filter(user=request.user)

    portfolio_data = []
    total_investment = Decimal('0.00')
    total_value = Decimal('0.00')

    for p in portfolio:
        investment = p.average_price * p.quantity
        current_value = p.stock.price * p.quantity
        profit_loss = current_value - investment

        total_investment += investment
        total_value += current_value

        portfolio_data.append({
            'stock': p.stock,
            'quantity': p.quantity,
            'average_price': p.average_price,
            'investment': investment.quantize(Decimal('0.01')),
            'current_price': p.stock.price,
            'current_value': current_value.quantize(Decimal('0.01')),
            'profit_loss': profit_loss.quantize(Decimal('0.01')),
        })

    total_profit_loss = (total_value - total_investment).quantize(Decimal('0.01'))

    if request.method == 'POST':
        stock_id = request.POST.get('stock_id')
        quantity = int(request.POST.get('quantity'))
        action = request.POST.get('action')

        stock = Stock.objects.get(id=stock_id)

        if action == 'buy':
            portfolio_item, created = Portfolio.objects.get_or_create(user=request.user, stock=stock)
            if created:
                portfolio_item.quantity = quantity
                portfolio_item.average_price = stock.price
            else:
                total_quantity = portfolio_item.quantity + quantity
                portfolio_item.average_price = (
                    (portfolio_item.average_price * portfolio_item.quantity) + (stock.price * quantity)
                ) / total_quantity
                portfolio_item.quantity = total_quantity
            portfolio_item.save()

            Transaction.objects.create(
                user=request.user,
                stock=stock,
                quantity=quantity,
                price=stock.price,
                transaction_type='BUY'
            )

        elif action == 'sell':
            try:
                portfolio_item = Portfolio.objects.get(user=request.user, stock=stock)
                if portfolio_item.quantity >= quantity:
                    portfolio_item.quantity -= quantity
                    portfolio_item.save()

                    Transaction.objects.create(
                        user=request.user,
                        stock=stock,
                        quantity=quantity,
                        price=stock.price,
                        transaction_type='SELL'
                    )
                else:
                    return render(request, 'dashboard.html', {
                        'stocks': stocks,
                        'portfolio_data': portfolio_data,
                        'total_investment': total_investment,
                        'total_value': total_value,
                        'total_profit_loss': total_profit_loss,
                        'query': query,
                        'error': 'Not enough quantity to sell'
                    })
            except Portfolio.DoesNotExist:
                return render(request, 'dashboard.html', {
                    'stocks': stocks,
                    'portfolio_data': portfolio_data,
                    'total_investment': total_investment,
                    'total_value': total_value,
                    'total_profit_loss': total_profit_loss,
                    'query': query,
                    'error': 'You do not own this stock to sell'
                })

        return redirect('dashboard')

    return render(request, 'dashboard.html', {
        'stocks': stocks,
        'portfolio_data': portfolio_data,
        'total_investment': total_investment,
        'total_value': total_value,
        'total_profit_loss': total_profit_loss,
        'query': query
    })
@login_required
def transaction_history(request):
    query_date = request.GET.get('date', '')
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    if query_date:
        transactions = transactions.filter(date__date=query_date)

    return render(request, 'transaction_history.html', {
        'transactions': transactions,
        'query_date': query_date
    })

def get_live_price(request, symbol):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d", interval="1m")
        latest_price = data['Close'].iloc[-1]
        return JsonResponse({'price': float(latest_price)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def stock_detail(request, stock_id):
    stock = Stock.objects.get(id=stock_id)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))
        action = request.POST.get('action')
        live_price = Decimal(request.POST.get('price'))

        if action == 'buy':
            portfolio_item, created = Portfolio.objects.get_or_create(user=request.user, stock=stock)
            if created:
                portfolio_item.quantity = quantity
                portfolio_item.average_price = live_price
            else:
                total_quantity = portfolio_item.quantity + quantity
                portfolio_item.average_price = (
                    (portfolio_item.average_price * portfolio_item.quantity) + (live_price * quantity)
                ) / total_quantity
                portfolio_item.quantity = total_quantity
            portfolio_item.save()

            Transaction.objects.create(
                user=request.user,
                stock=stock,
                quantity=quantity,
                price=live_price,
                transaction_type='BUY'
            )

        elif action == 'sell':
            try:
                portfolio_item = Portfolio.objects.get(user=request.user, stock=stock)
                if portfolio_item.quantity >= quantity:
                    portfolio_item.quantity -= quantity
                    portfolio_item.save()

                    Transaction.objects.create(
                        user=request.user,
                        stock=stock,
                        quantity=quantity,
                        price=live_price,
                        transaction_type='SELL'
                    )
            except Portfolio.DoesNotExist:
                pass

        return redirect('dashboard')

    return render(request, 'stock_detail.html', {'stock': stock})

@csrf_exempt
def get_candlestick_data(request, symbol):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d", interval="1m")
        latest = data.iloc[-1]

        response_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'open': round(latest['Open'], 2),
            'high': round(latest['High'], 2),
            'low': round(latest['Low'], 2),
            'close': round(latest['Close'], 2),
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

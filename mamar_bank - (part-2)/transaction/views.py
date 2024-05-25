from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Transaction
from .constants import DEPOSIT,WITHDRAWAL,LOAN,LOANPAID
from .forms import TransactionForm,WithdrawForm,DepositForm,LoanRequestForm
from django.contrib import messages
from datetime import datetime, date
from django.db.models import Sum
from django.views import View
from django.urls import reverse_lazy
# Create your views here.


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transaction/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # template e context data pass kora
        context.update({
            'title': self.title
        })

        return context

    
    
class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        # if not account.initial_deposit_date:
        #     now = timezone.now()
        #     account.initial_deposit_date = now
        account.balance += amount # amount = 200, tar ager balance = 0 taka new balance = 0+200 = 200
        account.save(
            update_fields=[
                'balance'
            ]
        )

        messages.success(
            self.request,
            f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully'
        )
        return super().form_valid(form)


    

class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw'
    
    def get_initial(self):
        initial = {'transaction_type' : WITHDRAWAL}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance -= amount
        
        account.save(
            update_fields = ['balance']
        )
        messages.success(self.request, f"{amount}$ withdraw from your account")
        return super().form_valid(form)
    
    
class LoanRequestView(TransactionCreateMixin):
    title = 'Loan Request'
    form_class = LoanRequestForm
    
    def get_initial(self):
        initial = {'transaction_type' : LOAN}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        loan_count = Transaction.objects.filter(account=self.request.user.account, transaction_type=3, loan_approve=True).count()
        
        if loan_count >= 3:
            return HttpResponse("You already corssed your loan limit.")
        
        messages.success(self.request, f"Your loan request successfully sent to admin.")
        
        return super().form_valid(form)
    
    
class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = "transaction/transaction_report.html"
    model = Transaction
    balance = 0
    
    def get_queryset(self):
        
        queryset = super().get_queryset().filter(account = self.request.user.account)
        
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            queryset = queryset.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
            self.balance = Transaction.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
        
        return queryset.distinct()
            
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account' : self.request.user.account
        })
        return context
    

class payLoanView(LoginRequiredMixin, View):
    
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        
        if loan.loan_approve:
            user_account = loan.account
            if loan.amount <= user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.transaction_type = LOANPAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error(self.request, "Loan amount is greater than available balance")
                return redirect('loan_list')



class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transaction/loan_request.html"
    context_object_name = "loans"
    
    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account=user_account, transaction_type=LOAN)
        return queryset


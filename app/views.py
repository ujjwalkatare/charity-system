from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import trust_profile
from .auth import authentication ,authenticatio2
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.db.models import Sum
from django.contrib.auth import logout
from collections import defaultdict

from .models import trust_profile, Donation

# Create your views here.
def home(request):
    return render(request, 'index.html')

def donor_register(request):
    if request.method == "POST":
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        username = request.POST['username']
        password = request.POST['password']
        password1 = request.POST['password1']
        
        verify = authentication(first_name, last_name, password, password1)
        if verify == "success":
            user = User.objects.create_user(username=username, password=password)
            user.email = password1
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            messages.success(request, "Your Account has been Created.")
            return redirect("log_in")
        else:
            messages.error(request, verify)

    # Render the form with the current input values if there was an error
    return render(request, "donor_register.html", {
        'first_name': request.POST.get('fname', ''),
        'last_name': request.POST.get('lname', ''),
        'username': request.POST.get('username', ''),
        'password': request.POST.get('password', ''),
        'password1': request.POST.get('password1', '')
    })

from django.contrib.auth.models import User
from django.contrib import messages

def trust_register(request):
    if request.method == "POST":
        first_name = request.POST['fname']
        contact = request.POST['contact']
        address = request.POST['address']
        eth_address = request.POST['eth_address']
        username = request.POST['username']
        password = request.POST['password']
        password1 = request.POST['password1']

        # 🔴 CHECK IF USERNAME ALREADY EXISTS
        if User.objects.filter(username=username).exists():
            messages.error(request, "Email already registered. Please login.")
            return render(request, "trust_register.html", {
                'first_name': first_name,
                'contact': contact,
                'address': address,
                'eth_address': eth_address,
                'username': username
            })

        verify = authenticatio2(first_name, contact, password, password1)

        if verify == "success":
            user = User.objects.create_user(username=username, password=password)
            user.first_name = first_name
            user.save()

            profile = trust_profile.objects.create(
                user=user,
                contact_number=contact,
                address=address,
                eth_address=eth_address
            )

            messages.success(request, "Your Account has been Created.")
            return redirect("log_in")

        else:
            messages.error(request, verify)

    return render(request, "trust_register.html", {
        'first_name': request.POST.get('fname', ''),
        'contact': request.POST.get('contact', ''),
        'address': request.POST.get('address', ''),
        'eth_address': request.POST.get('eth_address', ''),
        'username': request.POST.get('username', ''),
        'password': request.POST.get('password', ''),
        'password1': request.POST.get('password1', '')
    })

def log_in(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # =================================================
        # 🔐 STEP 1: SUPER ADMIN CHECK (HARD-CODED)
        # =================================================
        if username == "Superadmin@gmail.com" and password == "Superadmin@123":
            # Create session flag for super admin
            request.session["is_superadmin"] = True
            messages.success(request, "Super Admin Login Successful!")
            return redirect("super_admin_dashboard")

        # =================================================
        # 👤 STEP 2: NORMAL DJANGO AUTH (Donor / Trust)
        # =================================================
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)

            # Check if user is a Trust
            trusts = trust_profile.objects.all()
            trust_users = [profile.user for profile in trusts]

            if user in trust_users:
                messages.success(request, "Trust Login Successful!")
                return redirect("trust_dashboard")
            else:
                messages.success(request, "User Login Successful!")
                return redirect("user_dashboard")

        else:
            messages.error(request, "Invalid Username or Password")
            return redirect("log_in")

    return render(request, "log_in.html")


def user_logout(request):
    logout(request)
    return redirect("log_in")

# Donar dashboard
from django.db.models import Sum

@login_required(login_url="log_in")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_dashboard(request):
    trusts = trust_profile.objects.all()

    donations = Donation.objects.filter(donor=request.user)

    total_eth = donations.aggregate(total=Sum("amount"))["total"] or 0
    ETH_TO_INR_RATE = 300000  # same rate everywhere

    context = {
        'fname': request.user.first_name,
        'trusts': trusts,
        'user_donation_total': round(total_eth * ETH_TO_INR_RATE, 2),  # INR
        'transaction_count': donations.count(),
    }

    return render(request, 'user_dashboard.html', context)


ETH_TO_INR_RATE = 300000  # static example (same as user side)


# Donations

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from web3 import Web3
import json
import hashlib

from .models import trust_profile, Donation

GANACHE_RPC = "http://127.0.0.1:7545"


@login_required(login_url="log_in")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@csrf_exempt
def donation(request):
    trusts = trust_profile.objects.all()

    # --------------------------------------------------
    # POST → VERIFY METAMASK TRANSACTION
    # --------------------------------------------------
    if request.method == "POST":

        # 1️⃣ Parse JSON safely
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON data"},
                status=400
            )

        trust_id = data.get("trust_id")
        tx_hash = data.get("tx_hash")

        if not trust_id or not tx_hash:
            return JsonResponse(
                {"error": "Missing trust_id or tx_hash"},
                status=400
            )

        # 2️⃣ Validate Trust
        try:
            trust = trust_profile.objects.get(id=trust_id)
        except trust_profile.DoesNotExist:
            return JsonResponse(
                {"error": "Trust not found"},
                status=404
            )

        # 3️⃣ Prevent Duplicate Transaction
        if Donation.objects.filter(tx_hash=tx_hash).exists():
            return JsonResponse(
                {"error": "Transaction already recorded"},
                status=409
            )

        # 4️⃣ Connect to Ganache
        web3 = Web3(Web3.HTTPProvider(GANACHE_RPC))

        if not web3.is_connected():
            return JsonResponse(
                {"error": "Blockchain not reachable"},
                status=500
            )

        # 5️⃣ Fetch Blockchain Transaction
        try:
            tx = web3.eth.get_transaction(tx_hash)
        except Exception:
            return JsonResponse(
                {"error": "Transaction not found on blockchain"},
                status=400
            )

        sender = tx.get("from")
        receiver = tx.get("to")

        if not receiver:
            return JsonResponse(
                {"error": "Transaction has no receiver"},
                status=400
            )

        # 6️⃣ Validate Receiver Address
        if receiver.lower() != trust.eth_address.lower():
            return JsonResponse(
                {"error": "Transaction receiver does not match trust address"},
                status=400
            )

        # 7️⃣ Get Amount (Wei → ETH)
        eth_amount = web3.from_wei(tx["value"], "ether")

        if eth_amount <= 0:
            return JsonResponse(
                {"error": "Invalid donation amount"},
                status=400
            )

        # 8️⃣ Generate Blockchain Integrity Hash
        integrity_hash = hashlib.sha256(
            f"{sender}{receiver}{eth_amount}{tx_hash}".encode()
        ).hexdigest()

        # 9️⃣ Save Donation (ETH = source of truth)
        Donation.objects.create(
            donor=request.user,
            trust=trust,
            amount=float(eth_amount),      # ✅ ETH ONLY
            tx_hash=tx_hash,
            integrity_hash=integrity_hash
        )

        return JsonResponse({
            "status": "success",
            "message": "Transaction verified and donation recorded",
            "tx_hash": tx_hash,
            "eth_amount": float(eth_amount),
            "sender": sender
        })

    # --------------------------------------------------
    # GET → RENDER DONATION PAGE
    # --------------------------------------------------
    return render(request, "donation.html", {
        "fname": request.user.first_name,
        "trusts": trusts
    })


from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.shortcuts import render
from django.db.models import Prefetch
from app.models import Donation, Utilization

ETH_TO_INR_RATE = 300000


@login_required(login_url="log_in")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def show_donation(request):

    # -----------------------------------------
    # 1️⃣ FETCH DONOR DONATIONS
    # -----------------------------------------
    donations = Donation.objects.filter(
        donor=request.user
    ).select_related(
        "trust"
    ).prefetch_related(
        Prefetch(
            "utilizations",
            queryset=Utilization.objects.filter(is_verified=True),
            to_attr="approved_utilizations"
        )
    ).order_by("-created_at")

    # -----------------------------------------
    # 2️⃣ BUILD DISPLAY DATA
    # -----------------------------------------
    donation_data = []

    for d in donations:
        donation_data.append({
            "trust_name": d.trust.user.first_name,
            "tx_hash": d.tx_hash,
            "eth_amount": d.amount,
            "inr_amount": round(d.amount * ETH_TO_INR_RATE, 2),
            "date": d.created_at,
            "utilizations": d.approved_utilizations  # ✅ ONLY APPROVED
        })

    # -----------------------------------------
    # 3️⃣ CONTEXT
    # -----------------------------------------
    context = {
        "fname": request.user.first_name,
        "donations": donation_data
    }

    return render(request, "show_donation.html", context)

# Trust Dashboard
ETH_TO_INR_RATE = 300000  # static example (same as user side)

@login_required(login_url="log_in")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def trust_dashboard(request):

    trust_user = request.user
    trust = trust_profile.objects.get(user=trust_user)

    # 🔵 Fetch all donations received by this trust
    donations = Donation.objects.filter(trust=trust).select_related("donor")

    # 🔵 Prepare donor list with INR conversion
    donor_list = []
    for d in donations:
        donor_list.append({
            "name": d.donor.first_name if d.donor else "Anonymous",
            "email": d.donor.username if d.donor else "N/A",
            "amount_eth": d.amount,
            "amount_inr": round(d.amount * ETH_TO_INR_RATE, 2),
            "tx_hash": d.tx_hash,
            "date": d.created_at,
        })

    donor_totals_eth = defaultdict(float)
    total_donated_eth = 0

    for donation in donations:
        donor_totals_eth[donation.donor] += donation.amount
        total_donated_eth += donation.amount

    total_donors = len(donor_totals_eth)

    # 🔵 Utilization (still INR-based)
    utilizations = Utilization.objects.filter(
        trust=trust
    ).order_by("-created_at")

    total_utilized_inr = utilizations.aggregate(
        total=Sum("amount_used")
    )["total"] or 0

    # 🔵 Convert ETH → INR for display
    total_donated_inr = round(total_donated_eth * ETH_TO_INR_RATE, 2)

    current_balance_inr = round(
        total_donated_inr - total_utilized_inr, 2
    )

    context = {

        # 🔵 TRUST BASIC INFO
        "fname": trust_user.first_name,
        "username": trust_user.username,
        "contact_number": trust.contact_number,
        "address": trust.address,

        # 🔵 TRUST IDENTITY
        "trust_eth_address": trust.eth_address,

        # 🔵 DISPLAY VALUES (INR ONLY)
        "balance": current_balance_inr,
        "total_donated_amount": total_donated_inr,
        "total_utilized_amount": round(total_utilized_inr, 2),

        # 🔵 META
        "total_donors": total_donors,
        "recent_utilizations": utilizations[:5],

        # 🔵 DONOR TABLE
        "donor_list": donor_list,
    }

    return render(request, "trust_dashboard.html", context)

from collections import defaultdict
from django.db.models import Sum
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control

ETH_TO_INR_RATE = 300000  # example static rate

@login_required(login_url="log_in")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def utilize_donation(request):
    trust_user = request.user
    trust = trust_profile.objects.get(user=trust_user)

    # --------------------------------
    # 1️⃣ LOAD DONATIONS (ETH STORED)
    # --------------------------------
    donations = Donation.objects.filter(trust=trust)

    # --------------------------------
    # 2️⃣ LOAD UTILIZATIONS (INR USED)
    # --------------------------------
    utilizations = Utilization.objects.filter(trust=trust)

    # --------------------------------
    # 3️⃣ UTILIZED INR PER DONATION
    # --------------------------------
    utilized_inr_per_donation = defaultdict(float)

    for u in utilizations:
        utilized_inr_per_donation[u.donation_id] += float(u.amount_used)

    # --------------------------------
    # 4️⃣ BUILD DROPDOWN DATA (INR)
    # --------------------------------
    received_donations = []
    total_remaining_inr = 0

    for d in donations:
        donated_inr = d.amount * ETH_TO_INR_RATE
        used_inr = utilized_inr_per_donation.get(d.id, 0)
        remaining_inr = round(donated_inr - used_inr, 2)

        if remaining_inr <= 0:
            continue

        received_donations.append({
            "donation_id": d.id,
            "tx_hash": d.tx_hash,
            "donor": d.donor,
            "amount_inr": remaining_inr
        })

        total_remaining_inr += remaining_inr

    # --------------------------------
    # 5️⃣ HANDLE POST
    # --------------------------------
    if request.method == "POST":
        donation_id = request.POST.get("tx_hash")  # holds donation.id
        used_inr = float(request.POST.get("used_amt"))
        purpose = request.POST.get("purpose")
        category = request.POST.get("category")
        proof = request.FILES.get("proof_image") or request.FILES.get("proof_bill")

        try:
            donation = Donation.objects.get(id=donation_id, trust=trust)
        except Donation.DoesNotExist:
            messages.error(request, "Invalid donation selected.")
            return redirect("utilize_donation")

        donated_inr = donation.amount * ETH_TO_INR_RATE
        already_used = utilized_inr_per_donation.get(donation.id, 0)
        available_inr = donated_inr - already_used

        if used_inr <= 0 or used_inr > available_inr:
            messages.error(request, "Amount exceeds available balance.")
            return redirect("utilize_donation")

        if not proof:
            messages.error(request, "At least one proof is required.")
            return redirect("utilize_donation")

        # --------------------------------
        # 6️⃣ SAVE UTILIZATION (MODEL SAFE)
        # --------------------------------
        Utilization.objects.create(
            donation=donation,
            trust=trust,
            amount_used=used_inr,
            purpose=purpose,
            category=category,
            proof=proof
        )

        messages.success(request, "Utilization recorded successfully.")
        return redirect("utilize_donation")

    # --------------------------------
    # 7️⃣ CONTEXT
    # --------------------------------
    total_donated_eth = donations.aggregate(
        total=Sum("amount")
    )["total"] or 0

    context = {
        "fname": trust_user.first_name,
        "received_donations": received_donations,
        "balance": round(total_remaining_inr, 2),
        "total_donated_amount": round(total_donated_eth * ETH_TO_INR_RATE, 2),
    }

    return render(request, "utilize_donation.html", context)

ETH_TO_INR_RATE = 300000

@login_required(login_url="log_in")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def show_utilization(request):

    trust_user = request.user
    trust = trust_profile.objects.get(user=trust_user)

    # DONATIONS (ETH)
    donations = Donation.objects.filter(trust=trust)

    total_donated_eth = donations.aggregate(
        total=Sum("amount")
    )["total"] or 0

    # CONVERT TO INR
    total_donated_inr = total_donated_eth * ETH_TO_INR_RATE


    # UTILIZATION (INR)
    utilizations = Utilization.objects.filter(
        trust=trust
    ).select_related("donation").order_by("-created_at")

    total_utilized_inr = utilizations.aggregate(
        total=Sum("amount_used")
    )["total"] or 0


    # CORRECT BALANCE
    current_balance = total_donated_inr - total_utilized_inr


    context = {
        "fname": trust_user.first_name,
        "utilizations": utilizations,

        "balance": round(current_balance, 2),
        "total_utilized_amount": round(total_utilized_inr, 2),
    }

    return render(request, "show_utilization.html", context)

# SUPER ADMIN DASHBOARD

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def super_admin_dashboard(request):

    # 🔐 SECURITY CHECK
    if not request.session.get("is_superadmin"):
        return redirect("log_in")

    # ---------------------------------------------------
    # 1️⃣ DONOR LIST (NAME, TOTAL DONATED, DONATION COUNT)
    # ---------------------------------------------------
    donors_data = []

    donors = User.objects.filter(
        is_superuser=False
    ).exclude(
        id__in=trust_profile.objects.values_list("user_id", flat=True)
    )

    for donor in donors:
        donor_donations = Donation.objects.filter(donor=donor)

        total_eth = donor_donations.aggregate(
            total=Sum("amount")
        )["total"] or 0

        donors_data.append({
            "donor_name": donor.first_name or donor.username,
            "donation_count": donor_donations.count(),
            "total_donated_inr": round(total_eth * ETH_TO_INR_RATE, 2),
        })

    # ---------------------------------------------------
    # 2️⃣ TRUST LIST (NAME, ETH ADDRESS, RECEIVED, UTILIZED)
    # ---------------------------------------------------
    trusts_data = []

    trusts = trust_profile.objects.all()

    for trust in trusts:
        donations = Donation.objects.filter(trust=trust)
        utilizations = Utilization.objects.filter(trust=trust)

        total_received_eth = donations.aggregate(
            total=Sum("amount")
        )["total"] or 0

        total_utilized_inr = utilizations.aggregate(
            total=Sum("amount_used")
        )["total"] or 0

        trusts_data.append({
            "trust_name": trust.user.first_name,
            "eth_address": trust.eth_address,
            "total_received_inr": round(total_received_eth * ETH_TO_INR_RATE, 2),
            "total_utilized_inr": round(total_utilized_inr, 2),
        })

    # ---------------------------------------------------
    # 3️⃣ CONTEXT
    # ---------------------------------------------------
    context = {
        "donors": donors_data,
        "trusts": trusts_data,
    }

    return render(request, "super_admin_dashboard.html", context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.views.decorators.cache import cache_control

from django.contrib.auth.models import User
from .models import Donation, Utilization, trust_profile

ETH_TO_INR_RATE = 300000


# ---------------------------------------------------
# 👑 SUPER ADMIN – DONATION & UTILIZATION TRACE PAGE
# ---------------------------------------------------
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def super_admin_transactions(request):

    # 🔐 SECURITY CHECK
    if not request.session.get("is_superadmin"):
        return redirect("log_in")

    donations_data = []

    donations = Donation.objects.select_related(
        "donor", "trust"
    ).prefetch_related("utilizations").order_by("-created_at")

    # ================================
    # STATISTICS
    # ================================

    total_donations = donations.count()

    all_utilizations = Utilization.objects.all()

    total_utilizations = all_utilizations.count()
    approved_utilizations = all_utilizations.filter(is_verified=True).count()
    pending_utilizations = all_utilizations.filter(is_verified=False).count()

    approval_rate = (
        (approved_utilizations / total_utilizations) * 100
        if total_utilizations > 0 else 0
    )

    total_eth = donations.aggregate(total=Sum("amount"))["total"] or 0
    total_inr_amount = round(total_eth * ETH_TO_INR_RATE, 2)

    total_eth_amount = total_eth

    average_donation = (
        total_inr_amount / total_donations
        if total_donations > 0 else 0
    )

    # ================================
    # DONATION DATA
    # ================================

    for donation in donations:

        utilizations = donation.utilizations.all()

        donation_inr = round(
            (donation.amount or 0) * ETH_TO_INR_RATE, 2
        )

        donations_data.append({

            "donation": donation,

            # Use first name instead of username
            "donor_name": (
                donation.donor.first_name
                if donation.donor and donation.donor.first_name
                else donation.donor.username
                if donation.donor else "Anonymous"
            ),

            "trust_name": (
                donation.trust.user.first_name
                if donation.trust and donation.trust.user
                else "Unknown"
            ),

            "eth_amount": donation.amount or 0,

            "inr_amount": donation_inr,

            "tx_hash": donation.tx_hash,

            "date": donation.created_at,

            "utilizations": utilizations,
        })

    # ================================
    # CONTEXT
    # ================================

    context = {

        "donations_data": donations_data,

        "total_donations": total_donations,

        "total_utilizations": total_utilizations,

        "approved_utilizations": approved_utilizations,

        "pending_utilizations": pending_utilizations,

        "approval_rate": round(approval_rate, 2),

        "total_inr_amount": total_inr_amount,

        "total_eth_amount": total_eth_amount,

        "average_donation": round(average_donation, 2),
    }

    return render(
        request,
        "super_admin_transactions.html",
        context
    )

# ---------------------------------------------------
# ✅ APPROVE UTILIZATION
# ---------------------------------------------------
def approve_utilization(request, utilization_id):
    if not request.session.get("is_superadmin"):
        return redirect("log_in")

    utilization = get_object_or_404(Utilization, id=utilization_id)

    utilization.is_verified = True
    utilization.verified_at = timezone.now()
    utilization.save()

    messages.success(request, "Utilization approved successfully.")
    return redirect("super_admin_transactions")


# ---------------------------------------------------
# ❌ REJECT UTILIZATION (OPTIONAL)
# ---------------------------------------------------
def reject_utilization(request, utilization_id):
    if not request.session.get("is_superadmin"):
        return redirect("log_in")

    utilization = get_object_or_404(Utilization, id=utilization_id)

    utilization.is_verified = False
    utilization.save()

    messages.error(request, "Utilization rejected.")
    return redirect("super_admin_transactions")
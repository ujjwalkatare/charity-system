from django.db import models
from django.contrib.auth.models import User

# 🔹 Trust / NGO Profile
class trust_profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    contact_number = models.CharField(max_length=50)
    address = models.CharField(max_length=200)

    # 🔗 Immutable blockchain identity of the trust
    eth_address = models.CharField(
        max_length=42,
        unique=True,
        help_text="Ethereum public wallet address of the trust (MetaMask)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username if self.user else self.eth_address

        return self.user.username if self.user else self.eth_address
class Donation(models.Model):
    donor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Registered donor (optional)"
    )

    trust = models.ForeignKey(
        trust_profile,
        on_delete=models.CASCADE,
        related_name="donations"
    )

    amount = models.FloatField(
        help_text="Amount donated (verified from blockchain)"
    )

    tx_hash = models.CharField(
        max_length=66,
        unique=True,
        help_text="Ethereum transaction hash (MetaMask / Ganache)"
    )

    # 🔐 DB integrity checksum (NOT a blockchain hash)
    integrity_hash = models.CharField(
        max_length=128,
        help_text="Derived checksum for DB integrity verification"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Donation ₹{self.amount} → {self.trust.eth_address[:10]}"


class Utilization(models.Model):
    donation = models.ForeignKey(
        Donation,
        on_delete=models.CASCADE,
        related_name="utilizations"
    )

    trust = models.ForeignKey(
        trust_profile,
        on_delete=models.CASCADE
    )

    amount_used = models.FloatField()
    purpose = models.CharField(max_length=500)
    category = models.CharField(max_length=50, default="Other")

    proof = models.ImageField(
        upload_to="utilization_proofs/",
        null=True,
        blank=True
    )

    # 🔐 ADMIN VERIFICATION FIELDS (NEW)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_utilizations"
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Used ₹{self.amount_used} for {self.purpose[:30]}"    

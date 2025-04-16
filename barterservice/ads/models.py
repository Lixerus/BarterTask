from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Ad(models.Model):
    
    CONDITION_CHOICES = [
        ('new', 'Новое'),
        ('used', 'Б/у'),
        ('broken', 'Требует ремонта'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ads')
    title = models.CharField(max_length=50)
    description = models.TextField(null=False, blank=True)
    image_url = models.URLField(blank=True, null=False)
    category = models.CharField(max_length=50)
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} ({self.category})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        indexes = [
            models.Index(fields=['category', 'condition']),
        ]


class ExchangeProposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('accepted', 'Принята'),
        ('rejected', 'Отклонена'),
    ]
    
    ad_sender = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='sent_proposals')
    ad_receiver = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='received_proposals')
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Предложение от {self.ad_sender.user} к {self.ad_receiver.user}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Предложение обмена'
        verbose_name_plural = 'Предложения обмена'
        constraints = [
            models.UniqueConstraint(fields=['ad_sender', 'ad_receiver'], name='unique_proposal')
        ]
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Ad, ExchangeProposal

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )


@pytest.fixture
def another_user(db):
    return User.objects.create_user(
        username='anotheruser',
        password='testpass123',
        email='another@example.com'
    )


@pytest.fixture
def test_ad(db, test_user):
    return Ad.objects.create(
        user=test_user,
        title='Test Ad',
        description='Test Description',
        category='books',
        condition='new'
    )


@pytest.fixture
def another_ad(db, another_user):
    return Ad.objects.create(
        user=another_user,
        title='Another Ad',
        description='Another Description',
        category='electronics',
        condition='used'
    )


@pytest.fixture
def test_proposal(db, test_ad, another_ad):
    return ExchangeProposal.objects.create(
        ad_sender=test_ad,
        ad_receiver=another_ad,
        comment='Test proposal'
    )


@pytest.mark.django_db
class TestAdAPI:
    def test_create_ad_authenticated(self, api_client, test_user):
        api_client.force_authenticate(user=test_user)
        url = reverse('exchange_api:ad-list')
        data = {
            'title': 'New Book',
            'description': 'Great condition',
            'category': 'books',
            'condition': 'used'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Ad.objects.count() == 1
        assert Ad.objects.get().title == 'New Book'

    def test_create_ad_unauthenticated(self, api_client):
        url = reverse('exchange_api:ad-list')
        data = {'title': 'New Book', 'description': 'Test'}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_ad_owner(self, api_client, test_user, test_ad):
        api_client.force_authenticate(user=test_user)
        url = reverse('exchange_api:ad-detail', args=[test_ad.id])
        data = {'title': 'Updated Title'}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        test_ad.refresh_from_db()
        assert test_ad.title == 'Updated Title'

    def test_update_ad_non_owner(self, api_client, another_user, test_ad):
        api_client.force_authenticate(user=another_user)
        url = reverse('exchange_api:ad-detail', args=[test_ad.id])
        response = api_client.patch(url, {'title': 'Hacked Title'})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_ad(self, api_client, test_user, test_ad):
        api_client.force_authenticate(user=test_user)
        url = reverse('exchange_api:ad-detail', args=[test_ad.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Ad.objects.count() == 0
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_search_ads(self, api_client : APIClient, test_ad, another_ad):
        url = reverse('exchange_api:ad-list')
        response = api_client.get(url, {'search': 'Test'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == test_ad.title

    def test_filter_ads(self, api_client, test_ad, another_ad):
        url = reverse('exchange_api:ad-list')
        response = api_client.get(url, {'category': 'electronics'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == another_ad.title


@pytest.mark.django_db
class TestExchangeProposalAPI:
    def test_create_proposal(self, api_client, test_user, test_ad, another_ad):
        api_client.force_authenticate(user=test_user)
        url = reverse('exchange_api:proposal-list')
        data = {
            'ad_sender': test_ad.id,
            'ad_receiver': another_ad.id,
            'comment': 'Test comment'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert ExchangeProposal.objects.count() == 1
        assert ExchangeProposal.objects.first().ad_sender == test_ad

    def test_create_proposal_non_owner(self, api_client, another_user, test_ad, another_ad):
        api_client.force_authenticate(user=another_user)
        url = reverse('exchange_api:proposal-list')
        data = {
            'ad_sender': test_ad.id,
            'ad_receiver': another_ad.id,
            'comment': 'Test comment'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert ExchangeProposal.objects.count() == 0

    @pytest.mark.parametrize("prop_status,expected_status",[("pending",status.HTTP_400_BAD_REQUEST),("accepted",status.HTTP_200_OK)])
    def test_update_proposal_status_reciever(self, api_client, another_user, test_proposal,prop_status,expected_status):
        api_client.force_authenticate(user=another_user)
        url = reverse('exchange_api:proposal-update', args=[test_proposal.id])
        response = api_client.put(url, {'status': prop_status})
        assert response.status_code == expected_status
        test_proposal.refresh_from_db()
        assert test_proposal.status == prop_status

    @pytest.mark.parametrize("prop_status,expected_status",[("pending",status.HTTP_400_BAD_REQUEST),("rejected",status.HTTP_200_OK)])
    def test_update_proposal_status_sender(self, api_client, test_user, test_proposal,prop_status,expected_status):
        api_client.force_authenticate(user=test_user)
        url = reverse('exchange_api:proposal-update', args=[test_proposal.id])
        response = api_client.put(url, {'status': prop_status})
        assert response.status_code == expected_status
        test_proposal.refresh_from_db()
        assert test_proposal.status == prop_status

    @pytest.mark.parametrize("filters,amount",[("accepted",0),("pending",1)])
    def test_filter_proposals(self,api_client,test_user,test_proposal,filters,amount):
        api_client.force_authenticate(user=test_user)
        url = reverse('exchange_api:proposal-list',)
        response = api_client.get(url,  {'status': filters})
        assert response.status_code == 200
        assert len(response.data['results']) == amount
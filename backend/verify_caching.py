
import time
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from django.contrib.auth import get_user_model
from awards.views import AwardsViewSet

User = get_user_model()
factory = APIRequestFactory()

def setup_user():
    user, _ = User.objects.get_or_create(username='test_staff_cache', user_type='staff')
    return user

def test_caching():
    user = setup_user()
    view = AwardsViewSet.as_view({'get': 'list'})
    
    print("--- Testing Awards Page Caching ---")
    
    # First Request (Cold Cache)
    request1 = factory.get('/awards/', HTTP_HOST='localhost')
    force_authenticate(request1, user=user)
    
    start_time = time.time()
    response1 = view(request1)
    # We must render the response to trigger the actual work and caching
    if hasattr(response1, 'render'):
        response1.render()
    end_time = time.time()
    duration1 = end_time - start_time
    
    print(f"Request 1 (Cold): {duration1:.4f} seconds | Status: {response1.status_code}")
    
    # Second Request (Warm Cache)
    request2 = factory.get('/awards/', HTTP_HOST='localhost')
    force_authenticate(request2, user=user)
    
    start_time = time.time()
    response2 = view(request2)
    if hasattr(response2, 'render'):
        response2.render()
    end_time = time.time()
    duration2 = end_time - start_time
    
    print(f"Request 2 (Warm): {duration2:.4f} seconds | Status: {response2.status_code}")
    
    if duration2 < duration1:
        print(f"✅ PASSED: Request 2 was faster by {duration1 - duration2:.4f} seconds")
    else:
        print("⚠️ WARNING: Request 2 was not faster. Caching might not be working or dataset is too small.")

test_caching()

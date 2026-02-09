
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from django.contrib.auth import get_user_model
from candidates.views import (
    bulk_clear_candidate_data,
    bulk_change_candidate_center,
    clear_candidate_data,
    bulk_clear_enrollment_data
)

User = get_user_model()
factory = APIRequestFactory()

def setup_users():
    # Use defaults to ensure we don't fail if user exists, and update type if needed
    center_rep, _ = User.objects.update_or_create(
        username='test_verify_center_rep', 
        defaults={'user_type': 'center_representative'}
    )
    
    staff, _ = User.objects.update_or_create(
        username='test_verify_staff', 
        defaults={'user_type': 'staff'}
    )
    
    return center_rep, staff

def test_endpoint(view_func, user, name, data=None, pk=None):
    print(f"Testing {name} as {user.username} ({user.user_type})...")
    
    if pk:
         request = factory.post(f'/fake-url/{pk}/', data=data or {}, format='json')
    else:
        request = factory.post('/fake-url/', data=data or {}, format='json')
    
    force_authenticate(request, user=user)
    
    # Run loop
    try:
        if pk:
            response = view_func(request, pk)
        else:
            response = view_func(request)
            
        if response.status_code == status.HTTP_403_FORBIDDEN:
            if user.user_type == 'center_representative':
                print(f"✅ PASSED (Expected Forbidden): {response.status_code}")
            else:
                print(f"❌ FAILED (Unexpected Forbidden): {response.status_code} - Error: {response.data}")
        elif response.status_code == status.HTTP_200_OK:
            if user.user_type == 'center_representative':
                 print(f"❌ FAILED (Should be Forbidden): {response.status_code}")
            else:
                 print(f"✅ PASSED (Expected Allowed): {response.status_code}")
        else:
            # Other codes like 400 Bad Request are fine for Staff (as we don't send valid data)
            if user.user_type == 'center_representative':
                # If center rep gets 400, it means they passed the perm check!
                print(f"❌ FAILED (Should be 403, got {response.status_code}): {response.status_code}")
            else:
                print(f"✅ PASSED (Expected Outcome): {response.status_code}")
             
    except Exception as e:
        print(f"⚠️ Exception: {e}")

# Main
center_rep, staff = setup_users()

print("\n--- Testing Center Representative Restrictions ---")
test_endpoint(bulk_clear_candidate_data, center_rep, "bulk_clear_candidate_data", data={'candidate_ids': [1]})
test_endpoint(bulk_change_candidate_center, center_rep, "bulk_change_candidate_center", data={'candidate_ids': [1], 'new_center_id': 1})
test_endpoint(clear_candidate_data, center_rep, "clear_candidate_data", pk=999)
test_endpoint(bulk_clear_enrollment_data, center_rep, "bulk_clear_enrollment_data", data={'enrollment_ids': [1]})

print("\n--- Testing Staff Access (Should be allowed) ---")
test_endpoint(bulk_clear_candidate_data, staff, "bulk_clear_candidate_data", data={'candidate_ids': [1]})
test_endpoint(bulk_change_candidate_center, staff, "bulk_change_candidate_center", data={'candidate_ids': [1], 'new_center_id': 1})
test_endpoint(clear_candidate_data, staff, "clear_candidate_data", pk=999) 
test_endpoint(bulk_clear_enrollment_data, staff, "bulk_clear_enrollment_data", data={'enrollment_ids': [1]})

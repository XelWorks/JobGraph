import pytest
from app.services.matching.scoring import job_matching_service

def test_calculate_skill_score():
    """Verify Skill Score matching (40% weight)."""
    skills = ["Python", "FastAPI", "React", "Docker"]
    
    # 1. Full Match
    score_full = job_matching_service.calculate_skill_score(
        skills, 
        "We are looking for a developer with expertise in Python, FastAPI, and frontend React within Docker containers.",
        "Staff Python Engineer"
    )
    assert score_full == 100
    
    # 2. Partial Match (2 out of 4)
    score_partial = job_matching_service.calculate_skill_score(
        skills,
        "Experienced React developer who understands Docker deployment.",
        "React Web Developer"
    )
    assert score_partial == 50
    
    # 3. No match
    score_none = job_matching_service.calculate_skill_score(
        skills,
        "Looking for a Ruby on Rails backend software developer.",
        "Backend Developer"
    )
    assert score_none == 0

def test_calculate_experience_score():
    """Verify Experience/Role Score matching (30% weight)."""
    preferred_roles = ["Backend Engineer", "Software Architect"]
    
    # 1. Full role match
    score_full = job_matching_service.calculate_experience_score(preferred_roles, "Senior Backend Engineer")
    assert score_full == 100
    
    # 2. Partial word match
    score_partial = job_matching_service.calculate_experience_score(preferred_roles, "Systems Software Developer")
    assert score_partial == 60
    
    # 3. No match
    score_none = job_matching_service.calculate_experience_score(preferred_roles, "Product Manager")
    assert score_none == 0

def test_calculate_location_score():
    """Verify Location Score matching (15% weight)."""
    preferred_locations = ["Remote", "New York"]
    
    # 1. Match Location
    score_full = job_matching_service.calculate_location_score(preferred_locations, "New York City Office")
    assert score_full == 100
    
    # 2. Flexible Remote matches
    score_remote = job_matching_service.calculate_location_score(preferred_locations, "Work from anywhere (Remote)")
    assert score_remote == 100
    
    # 3. No match
    score_none = job_matching_service.calculate_location_score(preferred_locations, "San Francisco, CA")
    assert score_none == 0

def test_calculate_salary_score():
    """Verify Salary Score matching (15% weight)."""
    target_salary = 120000
    
    # 1. Salary matches or exceeds
    score_exceeds = job_matching_service.calculate_salary_score(
        target_salary,
        "Competitive salary of $135,000 - $150k annually."
    )
    assert score_exceeds == 100
    
    # 2. Salary is below target (e.g. $100,000 max vs $120,000 target = 83%)
    score_below = job_matching_service.calculate_salary_score(
        target_salary,
        "Offering up to $100k for this role."
    )
    assert score_below == 83
    
    # 3. No salary markers extracted (returns neutral 80)
    score_neutral = job_matching_service.calculate_salary_score(
        target_salary,
        "Great benefits and perks."
    )
    assert score_neutral == 80

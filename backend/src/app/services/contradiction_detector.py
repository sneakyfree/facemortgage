"""
Borrower Profile Contradiction Detection.

Detects inconsistencies in borrower intake data to ensure
accurate matching and prevent processing issues.
"""

import logging
from typing import Optional
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)


class ContradictionSeverity(str, Enum):
    """Severity level of detected contradiction."""
    WARNING = "warning"  # Minor issue, can proceed
    ERROR = "error"      # Must be resolved before proceeding


class Contradiction(BaseModel):
    """A detected contradiction in borrower data."""
    field: str
    message: str
    severity: ContradictionSeverity
    suggestion: Optional[str] = None


class ContradictionDetector:
    """
    Detects logical contradictions in borrower intake data.
    
    Examples:
    - Refinance selected but no current property
    - VA eligibility claimed without veteran status
    - Loan amount exceeds jumbo limit without jumbo specialty
    - First-time buyer with current property
    """
    
    @classmethod
    def detect(cls, profile: dict) -> list[Contradiction]:
        """
        Detect contradictions in borrower profile data.
        
        Args:
            profile: Dictionary of borrower intake data
            
        Returns:
            List of detected contradictions
        """
        contradictions = []
        
        # Rule 1: Refinance requires current property
        if profile.get("loan_purpose") == "refinance":
            if not profile.get("current_property_address") and not profile.get("current_property"):
                contradictions.append(Contradiction(
                    field="loan_purpose",
                    message="Refinance selected but no current property specified",
                    severity=ContradictionSeverity.ERROR,
                    suggestion="Please provide your current property address for refinance",
                ))
        
        # Rule 2: Cash-out refinance requires equity
        if profile.get("loan_purpose") == "cash_out":
            if profile.get("current_loan_balance") and profile.get("current_property_value"):
                ltv = (profile["current_loan_balance"] / profile["current_property_value"]) * 100
                if ltv > 80:
                    contradictions.append(Contradiction(
                        field="current_loan_balance",
                        message=f"Current LTV ({ltv:.0f}%) too high for cash-out refinance",
                        severity=ContradictionSeverity.WARNING,
                        suggestion="Cash-out typically requires 80% or lower LTV",
                    ))
        
        # Rule 3: VA eligibility requires veteran status
        if profile.get("va_eligible") or profile.get("loan_type") == "va":
            if not profile.get("veteran_status") and not profile.get("is_veteran"):
                contradictions.append(Contradiction(
                    field="va_eligible",
                    message="VA loan eligibility claimed but veteran status not confirmed",
                    severity=ContradictionSeverity.ERROR,
                    suggestion="Please confirm military service status for VA loan",
                ))
        
        # Rule 4: Jumbo loan threshold
        conforming_limit = 766_550  # 2024 limit for most areas
        if profile.get("loan_amount") and profile["loan_amount"] > conforming_limit:
            if profile.get("loan_type") and "jumbo" not in profile["loan_type"].lower():
                contradictions.append(Contradiction(
                    field="loan_amount",
                    message=f"Loan amount ${profile['loan_amount']:,} exceeds conforming limit",
                    severity=ContradictionSeverity.WARNING,
                    suggestion="This loan will require jumbo financing",
                ))
        
        # Rule 5: First-time buyer inconsistency
        if profile.get("first_time_buyer") or profile.get("is_first_time_buyer"):
            if profile.get("current_property") or profile.get("owns_current_home"):
                contradictions.append(Contradiction(
                    field="first_time_buyer",
                    message="First-time buyer status conflicts with current property ownership",
                    severity=ContradictionSeverity.WARNING,
                    suggestion="First-time buyer programs may not apply if you currently own",
                ))
        
        # Rule 6: Income vs loan amount reasonability
        if profile.get("annual_income") and profile.get("loan_amount"):
            dti_estimate = (profile["loan_amount"] * 0.006) / (profile["annual_income"] / 12) * 100
            if dti_estimate > 50:
                contradictions.append(Contradiction(
                    field="loan_amount",
                    message=f"Estimated DTI ({dti_estimate:.0f}%) may exceed qualification limits",
                    severity=ContradictionSeverity.WARNING,
                    suggestion="Consider a lower loan amount or include co-borrower income",
                ))
        
        # Rule 7: HELOC requires existing equity
        if profile.get("loan_purpose") == "heloc":
            if not profile.get("current_property"):
                contradictions.append(Contradiction(
                    field="loan_purpose",
                    message="HELOC requires existing property with equity",
                    severity=ContradictionSeverity.ERROR,
                    suggestion="HELOC is only available for existing homeowners",
                ))
        
        # Rule 8: Investment property with FHA/VA
        if profile.get("property_use") == "investment":
            if profile.get("loan_type") in ["fha", "va"]:
                contradictions.append(Contradiction(
                    field="loan_type",
                    message=f"{profile['loan_type'].upper()} loans not available for investment property",
                    severity=ContradictionSeverity.ERROR,
                    suggestion="Investment properties require conventional or portfolio financing",
                ))
        
        # Rule 9: Timeline vs pre-approval status
        if profile.get("timeline") == "immediate":
            if not profile.get("pre_approved") and not profile.get("has_preapproval"):
                contradictions.append(Contradiction(
                    field="timeline",
                    message="Immediate timeline but no pre-approval on file",
                    severity=ContradictionSeverity.WARNING,
                    suggestion="Getting pre-approved will strengthen offers",
                ))
        
        # Rule 10: Credit score vs loan type compatibility
        if profile.get("credit_score"):
            score = profile["credit_score"]
            loan_type = profile.get("loan_type", "").lower()
            
            if loan_type == "conventional" and score < 620:
                contradictions.append(Contradiction(
                    field="credit_score",
                    message=f"Credit score {score} below typical conventional minimum (620)",
                    severity=ContradictionSeverity.WARNING,
                    suggestion="Consider FHA loan (580+) or credit improvement first",
                ))
            elif loan_type == "fha" and score < 580:
                contradictions.append(Contradiction(
                    field="credit_score",
                    message=f"Credit score {score} may require 10% down for FHA",
                    severity=ContradictionSeverity.WARNING,
                    suggestion="Scores below 580 require larger down payment",
                ))
        
        logger.info(f"Contradiction detection found {len(contradictions)} issues")
        return contradictions
    
    @classmethod
    def validate_intake(cls, profile: dict) -> dict:
        """
        Validate intake data and return structured result.
        
        Returns:
            {
                "valid": bool,
                "can_proceed": bool,
                "contradictions": list,
                "error_count": int,
                "warning_count": int,
            }
        """
        contradictions = cls.detect(profile)
        
        error_count = sum(1 for c in contradictions if c.severity == ContradictionSeverity.ERROR)
        warning_count = sum(1 for c in contradictions if c.severity == ContradictionSeverity.WARNING)
        
        return {
            "valid": len(contradictions) == 0,
            "can_proceed": error_count == 0,
            "contradictions": [c.model_dump() for c in contradictions],
            "error_count": error_count,
            "warning_count": warning_count,
        }

"""
Blockers and Unlockers Engine for FaceMortgage.

Implements the DNA Strand "Blockers/Unlockers" pattern:
- Identifies obstacles preventing loan approval
- Provides actionable "fix list" with prioritized steps
- Categories: Credit, DTI, State License, Timeline, Documentation
- Priority levels: Quick Win (24h), 30 Days, 90 Days
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class BlockerCategory(str, Enum):
    """Categories of loan approval blockers."""
    CREDIT = "credit"
    DTI = "dti"
    STATE_LICENSE = "state_license"
    TIMELINE = "timeline"
    DOCUMENTATION = "documentation"
    PROPERTY = "property"
    INCOME = "income"


class BlockerPriority(str, Enum):
    """Priority levels for fixing blockers."""
    QUICK_WIN = "quick_win"  # Can be fixed in 24 hours
    THIRTY_DAYS = "30_days"  # Requires 30 days to fix
    NINETY_DAYS = "90_days"  # Requires 90+ days to fix


class Blocker(BaseModel):
    """A specific issue blocking loan approval."""
    id: str
    category: BlockerCategory
    title: str
    description: str
    severity: int = Field(ge=1, le=10)  # 1-10, 10 is most severe
    priority: BlockerPriority
    can_proceed: bool  # Can still get a loan despite this blocker?


class Unlocker(BaseModel):
    """An action to resolve a blocker."""
    blocker_id: str
    action: str
    detailed_steps: list[str]
    estimated_time: str  # e.g., "1-2 days", "30 days"
    resources: list[str]  # Links, documents, contacts
    success_probability: float = Field(ge=0, le=1)


class BlockerAnalysis(BaseModel):
    """Complete analysis of a borrower's blockers and unlockers."""
    borrower_id: Optional[str]
    analyzed_at: datetime
    total_blockers: int
    blocking_approval: int  # Blockers that prevent any loan
    limiting_options: int   # Blockers that limit loan types
    
    blockers: list[Blocker]
    unlockers: list[Unlocker]
    
    quick_wins: list[Unlocker]
    thirty_day_fixes: list[Unlocker]
    ninety_day_fixes: list[Unlocker]
    
    recommended_loan_types: list[str]
    overall_readiness_score: int = Field(ge=0, le=100)


class BlockersUnlockersEngine:
    """
    Analyzes borrower profile to identify blockers and provide actionable fixes.
    
    Implements the DNA Strand principle of "Why Not + What To Do Next".
    """
    
    # Credit score thresholds by loan type
    CREDIT_THRESHOLDS = {
        "conventional": 620,
        "fha": 580,
        "va": 580,
        "usda": 640,
        "jumbo": 700,
    }
    
    # Maximum DTI by loan type
    DTI_THRESHOLDS = {
        "conventional": 43,
        "fha": 50,
        "va": 60,
        "usda": 41,
        "jumbo": 43,
    }
    
    @classmethod
    def analyze(
        cls,
        credit_score: Optional[int] = None,
        dti_ratio: Optional[float] = None,
        state: Optional[str] = None,
        timeline_days: Optional[int] = None,
        employment_type: Optional[str] = None,  # w2, self_employed, retired
        years_employment: Optional[int] = None,
        has_gift_funds: bool = False,
        property_type: Optional[str] = None,
        loan_purpose: str = "purchase",
        loan_amount: Optional[int] = None,
        borrower_id: Optional[str] = None,
    ) -> BlockerAnalysis:
        """
        Analyze borrower profile and generate blockers/unlockers.
        
        Returns a complete analysis with prioritized fix list.
        """
        blockers = []
        unlockers = []
        blocking_count = 0
        limiting_count = 0
        recommended_types = ["conventional", "fha", "va", "usda", "jumbo"]
        
        # === Credit Score Analysis ===
        if credit_score is not None:
            if credit_score < 500:
                blockers.append(Blocker(
                    id="credit_severe",
                    category=BlockerCategory.CREDIT,
                    title="Credit Score Too Low",
                    description=f"Credit score of {credit_score} is below minimum for all loan programs (580+)",
                    severity=10,
                    priority=BlockerPriority.NINETY_DAYS,
                    can_proceed=False,
                ))
                unlockers.append(Unlocker(
                    blocker_id="credit_severe",
                    action="Rebuild credit score to 580+",
                    detailed_steps=[
                        "Get a secured credit card and use responsibly",
                        "Pay all bills on time for 6+ months",
                        "Reduce credit utilization below 30%",
                        "Dispute any errors on credit report",
                        "Consider credit counseling"
                    ],
                    estimated_time="6-12 months",
                    resources=[
                        "https://www.annualcreditreport.com",
                        "Contact credit counseling agency"
                    ],
                    success_probability=0.65,
                ))
                blocking_count += 1
                recommended_types = []
                
            elif credit_score < 580:
                blockers.append(Blocker(
                    id="credit_low",
                    category=BlockerCategory.CREDIT,
                    title="Credit Score Limits Options",
                    description=f"Credit score of {credit_score} only qualifies for limited programs",
                    severity=8,
                    priority=BlockerPriority.NINETY_DAYS,
                    can_proceed=False,
                ))
                unlockers.append(Unlocker(
                    blocker_id="credit_low",
                    action="Improve credit score to 580+ for FHA eligibility",
                    detailed_steps=[
                        "Pay down credit card balances",
                        "Become an authorized user on good account",
                        "Request goodwill deletions for late payments"
                    ],
                    estimated_time="3-6 months",
                    resources=["Request credit report at annualcreditreport.com"],
                    success_probability=0.75,
                ))
                blocking_count += 1
                recommended_types = []
                
            elif credit_score < 620:
                blockers.append(Blocker(
                    id="credit_limited",
                    category=BlockerCategory.CREDIT,
                    title="Limited to FHA/VA Loans",
                    description=f"Credit score of {credit_score} qualifies for FHA (580+) but not Conventional (620+)",
                    severity=5,
                    priority=BlockerPriority.THIRTY_DAYS,
                    can_proceed=True,
                ))
                unlockers.append(Unlocker(
                    blocker_id="credit_limited",
                    action="Boost credit to 620 for Conventional loan access",
                    detailed_steps=[
                        "Pay down revolving balances to under 10%",
                        "Avoid new credit applications",
                        "Consider rapid rescore with lender"
                    ],
                    estimated_time="30-60 days",
                    resources=["Ask LO about rapid rescore options"],
                    success_probability=0.80,
                ))
                limiting_count += 1
                recommended_types = ["fha", "va"]
                
            elif credit_score < 700:
                blockers.append(Blocker(
                    id="credit_moderate",
                    category=BlockerCategory.CREDIT,
                    title="Higher Rates May Apply",
                    description=f"Credit score of {credit_score} qualifies but may not get best rates",
                    severity=3,
                    priority=BlockerPriority.QUICK_WIN,
                    can_proceed=True,
                ))
                unlockers.append(Unlocker(
                    blocker_id="credit_moderate",
                    action="Quick credit boost for better rates",
                    detailed_steps=[
                        "Pay down credit cards before closing",
                        "Don't close old accounts"
                    ],
                    estimated_time="1-7 days",
                    resources=["Calculator: Credit utilization impact"],
                    success_probability=0.90,
                ))
                if loan_amount and loan_amount > 766550:  # 2024 conforming limit
                    recommended_types = ["conventional", "fha", "va"]
        
        # === DTI Analysis ===
        if dti_ratio is not None:
            if dti_ratio > 60:
                blockers.append(Blocker(
                    id="dti_severe",
                    category=BlockerCategory.DTI,
                    title="Debt-to-Income Too High",
                    description=f"DTI of {dti_ratio:.0f}% exceeds maximum for all loan types (60%)",
                    severity=9,
                    priority=BlockerPriority.THIRTY_DAYS,
                    can_proceed=False,
                ))
                unlockers.append(Unlocker(
                    blocker_id="dti_severe",
                    action="Reduce DTI below 50%",
                    detailed_steps=[
                        "Pay off smallest debts first (snowball method)",
                        "Increase documented income if possible",
                        "Consider a co-borrower with income",
                        "Wait for existing debts to pay down"
                    ],
                    estimated_time="30-90 days",
                    resources=["Debt payoff calculator"],
                    success_probability=0.60,
                ))
                blocking_count += 1
                
            elif dti_ratio > 50:
                blockers.append(Blocker(
                    id="dti_high",
                    category=BlockerCategory.DTI,
                    title="DTI Limits Options",
                    description=f"DTI of {dti_ratio:.0f}% limits you to VA loans (up to 60%)",
                    severity=7,
                    priority=BlockerPriority.THIRTY_DAYS,
                    can_proceed=True,
                ))
                unlockers.append(Unlocker(
                    blocker_id="dti_high",
                    action="Reduce DTI to 43% for more options",
                    detailed_steps=[
                        "Pay down car loan or credit cards",
                        "Avoid new debt before closing"
                    ],
                    estimated_time="30-60 days",
                    resources=[],
                    success_probability=0.70,
                ))
                limiting_count += 1
                recommended_types = ["va"]
                
            elif dti_ratio > 43:
                blockers.append(Blocker(
                    id="dti_moderate",
                    category=BlockerCategory.DTI,
                    title="DTI Requires Exception",
                    description=f"DTI of {dti_ratio:.0f}% may require compensating factors",
                    severity=4,
                    priority=BlockerPriority.QUICK_WIN,
                    can_proceed=True,
                ))
                unlockers.append(Unlocker(
                    blocker_id="dti_moderate",
                    action="Prepare compensating factors documentation",
                    detailed_steps=[
                        "Document reserves (6+ months payments)",
                        "Show strong credit history",
                        "Highlight stable employment"
                    ],
                    estimated_time="1-3 days",
                    resources=["Work with LO on exception request"],
                    success_probability=0.85,
                ))
                limiting_count += 1
        
        # === Timeline Analysis ===
        if timeline_days is not None:
            if timeline_days < 21:
                blockers.append(Blocker(
                    id="timeline_rushed",
                    category=BlockerCategory.TIMELINE,
                    title="Closing Timeline Too Short",
                    description=f"Closing in {timeline_days} days is very aggressive",
                    severity=6,
                    priority=BlockerPriority.QUICK_WIN,
                    can_proceed=True,
                ))
                unlockers.append(Unlocker(
                    blocker_id="timeline_rushed",
                    action="Prioritize fast-close specialists",
                    detailed_steps=[
                        "Match with LOs who average <21 day closes",
                        "Have all documents ready immediately",
                        "Be responsive to all requests same-day"
                    ],
                    estimated_time="Immediate",
                    resources=["Filter: Fast Close Specialists"],
                    success_probability=0.75,
                ))
        
        # === Self-Employment Analysis ===
        if employment_type == "self_employed":
            if years_employment is None or years_employment < 2:
                blockers.append(Blocker(
                    id="self_emp_short",
                    category=BlockerCategory.INCOME,
                    title="Self-Employment History Too Short",
                    description="Most lenders require 2+ years of self-employment",
                    severity=7,
                    priority=BlockerPriority.NINETY_DAYS,
                    can_proceed=False,
                ))
                unlockers.append(Unlocker(
                    blocker_id="self_emp_short",
                    action="Document self-employment income",
                    detailed_steps=[
                        "Wait until 2 years of tax returns available",
                        "Look for bank statement loan programs",
                        "Consider portfolio lenders"
                    ],
                    estimated_time="Variable",
                    resources=["Ask LO about bank statement loans"],
                    success_probability=0.50,
                ))
                blocking_count += 1
            else:
                blockers.append(Blocker(
                    id="self_emp_docs",
                    category=BlockerCategory.DOCUMENTATION,
                    title="Self-Employment Documentation Required",
                    description="Self-employed borrowers need additional documentation",
                    severity=3,
                    priority=BlockerPriority.QUICK_WIN,
                    can_proceed=True,
                ))
                unlockers.append(Unlocker(
                    blocker_id="self_emp_docs",
                    action="Prepare self-employment documentation",
                    detailed_steps=[
                        "Gather 2 years of personal and business tax returns",
                        "Get YTD profit & loss statement",
                        "Prepare business license and CPA letter"
                    ],
                    estimated_time="1-3 days",
                    resources=["Self-employed documentation checklist"],
                    success_probability=0.95,
                ))
        
        # === Gift Funds Analysis ===
        if has_gift_funds:
            blockers.append(Blocker(
                id="gift_seasoning",
                category=BlockerCategory.DOCUMENTATION,
                title="Gift Funds Need Documentation",
                description="Gift funds require donor letter and seasoning",
                severity=3,
                priority=BlockerPriority.QUICK_WIN,
                can_proceed=True,
            ))
            unlockers.append(Unlocker(
                blocker_id="gift_seasoning",
                action="Document gift funds properly",
                detailed_steps=[
                    "Get signed gift letter from donor",
                    "Show donor's ability to give (bank statement)",
                    "Transfer funds and wait 60 days (or document trail)"
                ],
                estimated_time="1-60 days depending on seasoning",
                resources=["Gift letter template"],
                success_probability=0.95,
            ))
        
        # === Property Type Analysis ===
        if property_type == "condo":
            blockers.append(Blocker(
                id="condo_approval",
                category=BlockerCategory.PROPERTY,
                title="Condo Approval Required",
                description="Condos require HOA review and approval",
                severity=4,
                priority=BlockerPriority.THIRTY_DAYS,
                can_proceed=True,
            ))
            unlockers.append(Unlocker(
                blocker_id="condo_approval",
                action="Verify condo is FHA/VA/Conventional approved",
                detailed_steps=[
                    "Check FHA condo approval database",
                    "Request condo questionnaire from HOA",
                    "Verify insurance and reserves"
                ],
                estimated_time="7-30 days",
                resources=["HUD FHA Condo Approval List"],
                success_probability=0.80,
            ))
        
        # === Categorize unlockers by priority ===
        quick_wins = [u for u in unlockers if 
                      any(b.id == u.blocker_id and b.priority == BlockerPriority.QUICK_WIN for b in blockers)]
        thirty_day = [u for u in unlockers if 
                      any(b.id == u.blocker_id and b.priority == BlockerPriority.THIRTY_DAYS for b in blockers)]
        ninety_day = [u for u in unlockers if 
                      any(b.id == u.blocker_id and b.priority == BlockerPriority.NINETY_DAYS for b in blockers)]
        
        # === Calculate readiness score ===
        base_score = 100
        for blocker in blockers:
            if not blocker.can_proceed:
                base_score -= blocker.severity * 5
            else:
                base_score -= blocker.severity * 2
        readiness_score = max(0, min(100, base_score))
        
        return BlockerAnalysis(
            borrower_id=borrower_id,
            analyzed_at=datetime.utcnow(),
            total_blockers=len(blockers),
            blocking_approval=blocking_count,
            limiting_options=limiting_count,
            blockers=blockers,
            unlockers=unlockers,
            quick_wins=quick_wins,
            thirty_day_fixes=thirty_day,
            ninety_day_fixes=ninety_day,
            recommended_loan_types=recommended_types,
            overall_readiness_score=readiness_score,
        )

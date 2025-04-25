import os
import json
import re  # Import re module
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# Load API key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize LLM
llm = ChatGroq(model="llama3-8b-8192", temperature=0)

# Function to extract valid JSON from LLM response
def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)  # Extract content between first '{' and last '}'
    if match:
        try:
            return json.loads(match.group())  # Convert extracted string to JSON
        except json.JSONDecodeError:
            return None
    return None

# Function to generate rule
def generate_rule(prompt):
    examples = [
    {
      "input": "If the students computed age is less than 18, display a message indicating parental consent is required.",
      "output": {
        "conditions": {
          "fact": "computed_age",
          "operator": "lessThan",
          "value": 18
        },
        "actions": {
          "message": "Parental consent is required."
        }
      }
    },
    {
      "input": "If the students residency status is 'out-of-state', display a message about additional tuition fees.",
      "output": {
        "conditions": {
          "fact": "residency_status",
          "operator": "equal",
          "value": "out-of-state"
        },
        "actions": {
          "message": "Additional tuition fees apply for out-of-state students."
        }
      }
    },
    {
      "input": "If the student has not provided a high school diploma or equivalent, display a message about required documentation.",
      "output": {
        "conditions": {
          "fact": "high_school_diploma_provided",
          "operator": "equal",
          "value": False
        },
        "actions": {
          "message": "Required documentation: High school diploma or equivalent."
        }
      }
    },
    {
        "input": "If Student Identifier Status (SB01) is an 'S', indicating there is an SSN, digits 1-3 cannot equal 000, 666, or be between 900-999, and digits 4-5 cannot equal 00, and digits 6-9 cannot equal 0000.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "SB01",
                "operator": "equal",
                "value": "S"
              },
              {
                "fact": "SB00",
                "operator": "notInRange",
                "value": ["000", "666", "900-999"],
                "position": "1-3"
              },
              {
                "fact": "SB00",
                "operator": "notEqual",
                "value": "00",
                "position": "4-5"
              },
              {
                "fact": "SB00",
                "operator": "notEqual",
                "value": "0000",
                "position": "6-9"
              }
            ]
          },
          "actions": {
            "message": "Invalid SSN format"
          }
        }
      },
      {
        "input": "If Student Education Status (SB11) = 10000, then the student’s computed age must be less than 22.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "SB11",
                "operator": "equal",
                "value": 10000
              },
              {
                "fact": "computed_age",
                "operator": "lessThan",
                "value": 22
              }
            ]
          },
          "actions": {
            "message": "Student age must be less than 22."
          }
        }
      },
      {
        "input": "If this field is coded as 7YYYY, 7XXXX, 8YYYY, or 8XXXX, then Student Enrollment Status (SB15) must not be coded as 1.",
        "output": {
          "conditions": {
            "any": [
              {
                "fact": "field_value",
                "operator": "in",
                "value": ["7YYYY", "7XXXX", "8YYYY", "8XXXX"]
              }
            ]
          },
          "actions": {
            "fact": "SB15",
            "operator": "notEqual",
            "value": "1"
          }
        }
      },
      {
        "input": "If this field = 10000 (Special Admit in K-12), then Student Enrollment Status (SB15) must be coded as 'Y' and the student’s computed age (from Birth Date (SB03)) must be less than 22.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "field_value",
                "operator": "equal",
                "value": 10000
              },
              {
                "fact": "SB15",
                "operator": "equal",
                "value": "Y"
              },
              {
                "fact": "computed_age",
                "operator": "lessThan",
                "value": 22
              }
            ]
          },
          "actions": {
            "message": "Special Admit in K-12: Enrollment status must be 'Y' and age must be < 22."
          }
        }
      },
      {
        "input": "If this field = 10000 (Special Admit in K-12), then Student High School Last (SB12) must be coded all 'Y's.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "field_value",
                "operator": "equal",
                "value": 10000
              }
            ]
          },
          "actions": {
            "fact": "SB12",
            "operator": "equal",
            "value": "YYYY"
          }
        }
      },
      {
        "input": "This element can be coded as Y’s only if the age computed using data in Student Birth Date (SB03) is greater than 21 or Student Education Status (SB11) is coded as 10000 (Special Admit).",
        "output": {
          "conditions": {
            "any": [
              {
                "fact": "computed_age",
                "operator": "greaterThan",
                "value": 21
              },
              {
                "fact": "SB11",
                "operator": "equal",
                "value": 10000
              }
            ]
          },
          "actions": {
            "fact": "element",
            "operator": "equal",
            "value": "Y"
          }
        }
      },
      {
        "input": "If Student Education Status (SB11) is coded as 7YYYY, 7XXXX, 8YYYY, 8XXXX (indicating a degree), then SB15 must not be coded as '1' (first-time student).",
        "output": {
          "conditions": {
            "any": [
              {
                "fact": "SB11",
                "operator": "in",
                "value": ["7YYYY", "7XXXX", "8YYYY", "8XXXX"]
              }
            ]
          },
          "actions": {
            "fact": "SB15",
            "operator": "notEqual",
            "value": "1"
          }
        }
      },
      {
        "input": "If the student is enrolled in the current semester, retrieve the latest GPA from the student record system.",
        "output": {
          "conditions": {
            "fact": "enrollment_status",
            "operator": "equal",
            "value": "enrolled"
          },
          "actions": {
            "fact": "GPA",
            "source": "student_record_system",
            "action": "retrieve"
          }
        }
      },
      {
        "input": "If the student is on academic probation, retrieve their most recent transcript for review.",
        "output": {
          "conditions": {
            "fact": "academic_status",
            "operator": "equal",
            "value": "probation"
          },
          "actions": {
            "fact": "transcript",
            "source": "student_record_system",
            "action": "retrieve"
          }
        }
      },
      {
        "input": "If the student has applied for financial aid, check the external database for application status.",
        "output": {
          "conditions": {
            "fact": "financial_aid_application",
            "operator": "equal",
            "value": "submitted"
          },
          "actions": {
            "fact": "application_status",
            "source": "external_database",
            "action": "check"
          }
        }
      },
      {
        "input": "If the student has submitted a graduation application, verify that all course requirements are met.",
        "output": {
          "conditions": {
            "fact": "graduation_application",
            "operator": "equal",
            "value": "submitted"
          },
          "actions": {
            "fact": "course_requirements",
            "operator": "verify",
            "value": "met"
          }
        }
      },
      {
        "input": "If the student’s academic program is 'Nursing', ensure they have completed the required clinical hours.",
        "output": {
          "conditions": {
            "fact": "academic_program",
            "operator": "equal",
            "value": "Nursing"
          },
          "actions": {
            "fact": "clinical_hours",
            "operator": "verify",
            "value": "completed"
          }
        }
      },
      {
        "input": "If the student’s tuition payment is pending, verify that financial aid has been processed.",
        "output": {
          "conditions": {
            "fact": "tuition_payment",
            "operator": "equal",
            "value": "pending"
          },
          "actions": {
            "fact": "financial_aid",
            "operator": "verify",
            "value": "processed"
          }
        }
      },
      {
        "input": "If the student is a veteran, prioritize the processing of their enrollment application.",
        "output": {
          "conditions": {
            "fact": "student_status",
            "operator": "equal",
            "value": "veteran"
          },
          "actions": {
            "fact": "enrollment_application",
            "operator": "prioritize",
            "value": "processing"
          }
        }
      },
      {
        "input": "If the student is an international student, prioritize their visa documentation review.",
        "output": {
          "conditions": {
            "fact": "student_status",
            "operator": "equal",
            "value": "international"
          },
          "actions": {
            "fact": "visa_documentation",
            "operator": "prioritize",
            "value": "review"
          }
        }
      },
      {
        "input": "If the student has a disability accommodation request, prioritize course registration accordingly.",
        "output": {
          "conditions": {
            "fact": "accommodation_request",
            "operator": "equal",
            "value": "true"
          },
          "actions": {
            "fact": "course_registration",
            "operator": "prioritize",
            "value": "adjustment"
          }
        }
      },
      {
        "input": "If the student’s last name starts with 'A', assign them to Advisor Group A.",
        "output": {
          "conditions": {
            "fact": "last_name",
            "operator": "startsWith",
            "value": "A"
          },
          "actions": {
            "fact": "advisor_group",
            "operator": "assign",
            "value": "A"
          }
        }
      },
      {
        "input": "If the student’s email domain is '.edu', classify them as a university-affiliated student.",
        "output": {
          "conditions": {
            "fact": "email",
            "operator": "endsWith",
            "value": ".edu"
          },
          "actions": {
            "fact": "student_affiliation",
            "operator": "classify",
            "value": "university"
          }
        }
      },
      {
        "input": "If the student’s major contains the word 'Engineering', assign them to the STEM academic group.",
        "output": {
          "conditions": {
            "fact": "major",
            "operator": "contains",
            "value": "Engineering"
          },
          "actions": {
            "fact": "academic_group",
            "operator": "assign",
            "value": "STEM"
          }
        }
      },
      {
        "input": "If the student is a new admit, check if orientation is completed. If not, prevent registration.",
        "output": {
          "conditions": {
            "fact": "student_status",
            "operator": "equal",
            "value": "new_admit"
          },
          "actions": {
            "fact": "orientation_completed",
            "operator": "check",
            "next_action": {
              "fact": "registration",
              "operator": "prevent",
              "condition": "not_completed"
            }
          }
        }
      },
      {
        "input": "If the student is taking an online course, check if they have completed the online readiness assessment.",
        "output": {
          "conditions": {
            "fact": "course_mode",
            "operator": "equal",
            "value": "online"
          },
          "actions": {
            "fact": "readiness_assessment",
            "operator": "check",
            "next_action": {
              "fact": "student_status",
              "operator": "update",
              "condition": "assessment_completed"
            }
          }
        }
      },
      {
        "input": "If the student has an outstanding library fine, check if it exceeds $50, and if so, place a hold on their record.",
        "output": {
          "conditions": {
            "fact": "library_fine",
            "operator": "greaterThan",
            "value": 50
          },
          "actions": {
            "fact": "student_record",
            "operator": "placeHold",
            "condition": "fine_exceeds_limit"
          }
        }
      },
      {
        "input": "If the student’s GPA is lower than 2.0, check if it has declined compared to the previous semester.",
        "output": {
          "conditions": {
            "fact": "current_GPA",
            "operator": "lessThan",
            "value": 2.0
          },
          "actions": {
            "fact": "GPA_trend",
            "operator": "compare",
            "value": "previous_GPA",
            "condition": "declined"
          }
        }
      },
      {
        "input": "If the student’s registered credit hours exceed their financial aid eligibility, flag for review.",
        "output": {
          "conditions": {
            "fact": "registered_credit_hours",
            "operator": "greaterThan",
            "value": "financial_aid_eligibility"
          },
          "actions": {
            "fact": "financial_aid_status",
            "operator": "flag",
            "value": "review_required"
          }
        }
      },
      {
        "input": "If the student’s expected graduation date is before the completion of required courses, trigger an alert.",
        "output": {
          "conditions": {
            "fact": "expected_graduation_date",
            "operator": "before",
            "value": "required_courses_completion"
          },
          "actions": {
            "fact": "graduation_status",
            "operator": "alert",
            "value": "course_completion_mismatch"
          }
        }
      },
      {
        "input": "If the student is flagged for academic probation, log the reason for audit purposes.",
        "output": {
          "conditions": {
            "fact": "academic_status",
            "operator": "equal",
            "value": "probation"
          },
          "actions": {
            "fact": "audit_log",
            "operator": "store",
            "value": "probation_reason"
          }
        }
      },
      {
        "input": "If a rule prevents course enrollment, store the reason in the student’s record.",
        "output": {
          "conditions": {
            "fact": "enrollment_status",
            "operator": "equal",
            "value": "prevented"
          },
          "actions": {
            "fact": "student_record",
            "operator": "store",
            "value": "enrollment_prevention_reason"
          }
        }
      },
      {
        "input": "If a financial aid application is denied, capture metadata for reporting.",
        "output": {
          "conditions": {
            "fact": "financial_aid_status",
            "operator": "equal",
            "value": "denied"
          },
          "actions": {
            "fact": "reporting_metadata",
            "operator": "capture",
            "value": "financial_aid_denial_reason"
          }
        }
      },
      {
        "input": "If the student registers after the deadline, apply a late registration fee.",
        "output": {
          "conditions": {
            "fact": "registration_date",
            "operator": "after",
            "value": "registration_deadline"
          },
          "actions": {
            "fact": "fee",
            "operator": "apply",
            "value": "late_registration_fee"
          }
        }
      },
      {
        "input": "If the student’s course drop occurs after the refund deadline, charge a partial fee.",
        "output": {
          "conditions": {
            "fact": "course_drop_date",
            "operator": "after",
            "value": "refund_deadline"
          },
          "actions": {
            "fact": "fee",
            "operator": "charge",
            "value": "partial_refund_fee"
          }
        }
      },
      {
        "input": "If the student does not log into the course system within the first week, send a reminder email.",
        "output": {
          "conditions": {
            "fact": "last_login_date",
            "operator": "after",
            "value": "course_start + 7 days"
          },
          "actions": {
            "fact": "notification",
            "operator": "send",
            "value": "reminder_email"
          }
        }
      },
      {
        "input": "If a student submits a withdrawal request within 7 days of the semester start, allow full tuition refund.",
        "output": {
          "conditions": {
            "fact": "withdrawal_request_date",
            "operator": "within",
            "value": "semester_start + 7 days"
          },
          "actions": {
            "fact": "tuition_refund",
            "operator": "allow",
            "value": "full"
          }
        }
      },
      {
        "input": "If a student has not completed their degree requirements within 6 years, notify them of academic standing policies.",
        "output": {
          "conditions": {
            "fact": "time_since_enrollment",
            "operator": "greaterThan",
            "value": "6 years"
          },
          "actions": {
            "fact": "notification",
            "operator": "send",
            "value": "academic_standing_policy_alert"
          }
        }
      },
      {
        "input": "If more than 5 students from the same major request course overrides, notify the department.",
        "output": {
          "conditions": {
            "fact": "course_override_requests",
            "operator": "greaterThan",
            "value": 5,
            "groupBy": "major"
          },
          "actions": {
            "fact": "notification",
            "operator": "send",
            "value": "department_alert"
          }
        }
      },
      {
        "input": "If the average GPA of a student’s last 3 semesters is below 2.5, recommend academic counseling.",
        "output": {
          "conditions": {
            "fact": "average_gpa_last_3_semesters",
            "operator": "lessThan",
            "value": 2.5
          },
          "actions": {
            "fact": "recommendation",
            "operator": "assign",
            "value": "academic_counseling"
          }
        }
      },
      {
        "input": "If more than 20% of students in a course withdraw, trigger a faculty review.",
        "output": {
          "conditions": {
            "fact": "course_withdrawal_percentage",
            "operator": "greaterThan",
            "value": 20
          },
          "actions": {
            "fact": "review",
            "operator": "trigger",
            "value": "faculty_review"
          }
        }
      },
      {
        "input": "If a student has more than 3 concurrent incomplete grades, flag for advisor review.",
        "output": {
          "conditions": {
            "fact": "incomplete_grades",
            "operator": "greaterThan",
            "value": 3
          },
          "actions": {
            "fact": "review",
            "operator": "flag",
            "value": "advisor_review"
          }
        }
      },
      {
        "input": "If more than 30% of students in a specific course fail, trigger a curriculum review.",
        "output": {
          "conditions": {
            "fact": "course_failure_percentage",
            "operator": "greaterThan",
            "value": 30
          },
          "actions": {
            "fact": "review",
            "operator": "trigger",
            "value": "curriculum_review"
          }
        }
      },
      {
        "input": "If the student’s declared major is \"Computer Science\" and they have not completed a programming prerequisite, block enrollment in advanced CS courses.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "declared_major",
                "operator": "equal",
                "value": "Computer Science"
              },
              {
                "fact": "programming_prerequisite",
                "operator": "notCompleted",
                "value": True
              }
            ]
          },
          "actions": {
            "fact": "enrollment",
            "operator": "block",
            "value": "advanced_CS_courses"
          }
        }
      },
      {
        "input": "If a student’s financial aid is pending and tuition is unpaid, defer payment deadline by 2 weeks.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "financial_aid_status",
                "operator": "equal",
                "value": "pending"
              },
              {
                "fact": "tuition_status",
                "operator": "equal",
                "value": "unpaid"
              }
            ]
          },
          "actions": {
            "fact": "payment_deadline",
            "operator": "defer",
            "value": "2_weeks"
          }
        }
      },
      {
        "input": "If a student is enrolled in an accelerated program and their GPA falls below 3.0, trigger a review.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "program_enrollment",
                "operator": "equal",
                "value": "accelerated"
              },
              {
                "fact": "GPA",
                "operator": "lessThan",
                "value": 3.0
              }
            ]
          },
          "actions": {
            "fact": "academic_review",
            "operator": "trigger",
            "value": "true"
          }
        }
      },
      {
        "input": "If a student has transfer credits and is enrolled in a prerequisite course, confirm credit transfer before allowing registration.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "transfer_credits",
                "operator": "greaterThan",
                "value": 0
              },
              {
                "fact": "course_enrollment",
                "operator": "in",
                "value": "prerequisite_courses"
              }
            ]
          },
          "actions": {
            "fact": "credit_transfer",
            "operator": "confirm",
            "value": "before_registration"
          }
        }
      },
      {
        "input": "If a student is in the honors program and their GPA drops below 3.5, revoke honors status.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "honors_program",
                "operator": "equal",
                "value": "enrolled"
              },
              {
                "fact": "GPA",
                "operator": "lessThan",
                "value": 3.5
              }
            ]
          },
          "actions": {
            "fact": "honors_status",
            "operator": "revoke",
            "value": "true"
          }
        }
      },
      {
        "input": "If the student is an international applicant, validate their visa status with the immigration database.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "applicant_status",
                "operator": "equal",
                "value": "international"
              }
            ]
          },
          "actions": {
            "fact": "visa_status",
            "operator": "validate",
            "source": "immigration_database"
          }
        }
      },
      {
        "input": "If the student is applying for an internship, check their work authorization with government records.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "application_type",
                "operator": "equal",
                "value": "internship"
              }
            ]
          },
          "actions": {
            "fact": "work_authorization",
            "operator": "check",
            "source": "government_records"
          }
        }
      },
      {
        "input": "If the student has a loan, verify repayment history with the national student loan database.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "loan_status",
                "operator": "equal",
                "value": "active"
              }
            ]
          },
          "actions": {
            "fact": "repayment_history",
            "operator": "verify",
            "source": "national_student_loan_database"
          }
        }
      },
      {
        "input": "If the student is receiving veteran benefits, cross-check eligibility with the VA database.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "benefits_status",
                "operator": "equal",
                "value": "veteran"
              }
            ]
          },
          "actions": {
            "fact": "eligibility",
            "operator": "cross-check",
            "source": "VA_database"
          }
        }
      },
      {
        "input": "If a student applies for a state grant, verify eligibility with the state education department database.",
        "output": {
          "conditions": {
            "all": [
              {
                "fact": "grant_application",
                "operator": "equal",
                "value": "state_grant"
              }
            ]
          },
          "actions": {
            "fact": "eligibility",
            "operator": "verify",
            "source": "state_education_department_database"
          }
        }
      }
  ]
  

    example_texts = "\n\n".join(
        f"Input: \"{example['input']}\"\nOutput: {json.dumps(example['output'], indent=2)}"
        for example in examples
    )

    query = f"""
    Convert the following natural language statement into a structured JSON rule format.

    Examples:
    {example_texts}

    Now, convert this: "{prompt}"
    """

    response = llm.invoke([HumanMessage(content=query)])
    rule_text = response.content.strip()

    # Log response for debugging
    print("LLM Response:", rule_text)

    # Extract and validate JSON
    rule_json = extract_json(rule_text)
    if rule_json:
        return rule_json
    else:
        return {
            "error": "Invalid JSON response",
            "raw_output": rule_text
        }

# Streamlit UI
st.title("AI-Powered Business Rules Engine")
user_prompt = st.text_area("Enter your rule in natural language:")

if st.button("Generate Rule"):
    if user_prompt:
        rule_json = generate_rule(user_prompt)
        st.json(rule_json)
    else:
        st.warning("Please enter a rule.")

"""Analytics Service (feature-based)
Moved from app/features/analytics/service.py with adjusted imports
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import logging

from ...shared.entities import Grade
from ...shared.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class AnalyticsService:
    async def calculate_user_cgpa(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        try:
            stmt = select(Grade).where(Grade.user_id == user_id)
            result = await db.execute(stmt)
            all_grades = list(result.scalars().all())

            if not all_grades:
                return {
                    "user_id": user_id,
                    "total_subjects": 0,
                    "total_credits": 0,
                    "cgpa": 0.0,
                    "semesters_completed": 0,
                    "semester_breakdown": [],
                }

            semester_data: dict[int, dict[str, Any]] = {}
            total_credits = 0
            total_grade_points = 0.0

            for grade in all_grades:
                semester = grade.semester
                if semester not in semester_data:
                    semester_data[semester] = {
                        "semester": semester,
                        "subjects": [],
                        "credits": 0,
                        "grade_points": 0.0,
                    }

                semester_data[semester]["subjects"].append(
                    {
                        "course_code": grade.course_code,
                        "course_name": grade.course_name,
                        "credits": grade.credits,
                        "grade": grade.grade,
                        "grade_points": grade.gpa_points,
                    }
                )

                semester_data[semester]["credits"] += grade.credits
                semester_data[semester]["grade_points"] += (grade.gpa_points * grade.credits)

                total_credits += grade.credits
                total_grade_points += (grade.gpa_points * grade.credits)

            semester_breakdown = []
            for sem_num in sorted(semester_data.keys()):
                sem_data = semester_data[sem_num]
                sgpa = sem_data["grade_points"] / sem_data["credits"] if sem_data["credits"] > 0 else 0.0
                semester_breakdown.append(
                    {
                        "semester": sem_num,
                        "subjects_count": len(sem_data["subjects"]),
                        "total_credits": sem_data["credits"],
                        "sgpa": round(sgpa, 2),
                        "subjects": sem_data["subjects"],
                    }
                )

            cgpa = total_grade_points / total_credits if total_credits > 0 else 0.0

            return {
                "user_id": user_id,
                "total_subjects": len(all_grades),
                "total_credits": total_credits,
                "cgpa": round(cgpa, 2),
                "semesters_completed": len(semester_data),
                "semester_breakdown": semester_breakdown,
            }

        except Exception as e:
            logger.error(f"CGPA calculation failed for user {user_id}: {str(e)}")
            raise DatabaseError(f"CGPA calculation failed: {str(e)}")

    async def get_semester_summary(self, db: AsyncSession, user_id: str, semester: int) -> Optional[Dict[str, Any]]:
        try:
            stmt = select(Grade).where(Grade.user_id == user_id, Grade.semester == semester)
            result = await db.execute(stmt)
            grades = list(result.scalars().all())

            if not grades:
                return None

            total_credits = sum(grade.credits for grade in grades)
            total_grade_points = sum(grade.gpa_points * grade.credits for grade in grades)
            sgpa = total_grade_points / total_credits if total_credits > 0 else 0.0

            subjects = [
                {
                    "course_code": grade.course_code,
                    "course_name": grade.course_name,
                    "credits": grade.credits,
                    "grade": grade.grade,
                    "grade_points": grade.gpa_points,
                }
                for grade in grades
            ]

            return {
                "user_id": user_id,
                "semester": semester,
                "subjects_count": len(subjects),
                "total_credits": total_credits,
                "sgpa": round(sgpa, 2),
                "subjects": subjects,
            }

        except Exception as e:
            logger.error(
                f"Semester summary failed for user {user_id}, semester {semester}: {str(e)}"
            )
            raise DatabaseError(f"Semester summary failed: {str(e)}")

    async def get_performance_analytics(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        try:
            cgpa_data = await self.calculate_user_cgpa(db, user_id)

            if cgpa_data["total_subjects"] == 0:
                return {"user_id": user_id, "message": "No grades found for analysis", "cgpa_data": cgpa_data}

            semester_breakdown = cgpa_data["semester_breakdown"]
            sgpa_values = [sem["sgpa"] for sem in semester_breakdown]

            performance_trends = {
                "highest_sgpa": max(sgpa_values) if sgpa_values else 0.0,
                "lowest_sgpa": min(sgpa_values) if sgpa_values else 0.0,
                "average_sgpa": round(sum(sgpa_values) / len(sgpa_values), 2) if sgpa_values else 0.0,
                "sgpa_trend": sgpa_values,
            }

            all_grades = []
            for sem in semester_breakdown:
                all_grades.extend([subject["grade"] for subject in sem["subjects"]])

            grade_distribution: dict[str, int] = {}
            for grade in all_grades:
                grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

            return {
                "user_id": user_id,
                "cgpa_data": cgpa_data,
                "performance_trends": performance_trends,
                "grade_distribution": grade_distribution,
                "total_semesters": len(semester_breakdown),
            }

        except Exception as e:
            logger.error(f"Performance analytics failed for user {user_id}: {str(e)}")
            raise DatabaseError(f"Performance analytics failed: {str(e)}")


analytics_service = AnalyticsService()

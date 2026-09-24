"""stage6 schema additions

Revision ID: 20260924_stage6_schema_additions
Revises: 20260924_stage1_foundation
Create Date: 2026-09-24 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260924_stage6_schema_additions"
down_revision = "20260924_stage1_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to tasks
    op.add_column("tasks", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("exception_id", sa.String(length=36), nullable=True))
    op.add_column("tasks", sa.Column("notice_case_id", sa.String(length=36), nullable=True))
    
    # Add foreign keys for the new columns
    op.create_foreign_key("fk_tasks_exception_id", "tasks", "exceptions", ["exception_id"], ["id"])
    op.create_foreign_key("fk_tasks_notice_case_id", "tasks", "notice_cases", ["notice_case_id"], ["id"])

    # Create drafts table
    op.create_table(
        "drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("notice_case_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("cited_sections", sa.JSON(), nullable=True),
        sa.Column("missing_information", sa.JSON(), nullable=True),
        sa.Column("approved_by", sa.String(length=36), nullable=True),
        sa.Column("approval_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["notice_case_id"], ["notice_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("drafts")
    
    op.drop_constraint("fk_tasks_notice_case_id", "tasks", type_="foreignkey")
    op.drop_constraint("fk_tasks_exception_id", "tasks", type_="foreignkey")
    
    op.drop_column("tasks", "notice_case_id")
    op.drop_column("tasks", "exception_id")
    op.drop_column("tasks", "description")

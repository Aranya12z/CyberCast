"""Initial database schema matching DATA_SCHEMA.md

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-18 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. crimes
    op.create_table(
        'crimes',
        sa.Column('crime_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('crime_type', sa.String(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('latitude', sa.Numeric(), nullable=False),
        sa.Column('longitude', sa.Numeric(), nullable=False),
        sa.Column('amount', sa.Numeric(), nullable=False),
        sa.PrimaryKeyConstraint('crime_id')
    )

    # 2. atms
    op.create_table(
        'atms',
        sa.Column('atm_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('latitude', sa.Numeric(), nullable=False),
        sa.Column('longitude', sa.Numeric(), nullable=False),
        sa.Column('bank', sa.String(), nullable=False),
        sa.Column('area', sa.String(), nullable=False),
        sa.Column('historical_risk_score', sa.Numeric(), server_default='0.0', nullable=False),
        sa.PrimaryKeyConstraint('atm_id')
    )

    # 3. transactions
    op.create_table(
        'transactions',
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('atm_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('amount', sa.Numeric(), nullable=False),
        sa.Column('account_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['atm_id'], ['atms.atm_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('transaction_id')
    )

    # 4. model_metadata
    op.create_table(
        'model_metadata',
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('trained_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('algorithm', sa.String(), nullable=False),
        sa.Column('eval_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('model_version')
    )

    # 5. predictions
    op.create_table(
        'predictions',
        sa.Column('prediction_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('crime_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('generated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['crime_id'], ['crimes.crime_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_version'], ['model_metadata.model_version']),
        sa.PrimaryKeyConstraint('prediction_id')
    )

    # 6. prediction_results
    op.create_table(
        'prediction_results',
        sa.Column('result_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('prediction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('atm_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_score', sa.Numeric(), nullable=False),
        sa.Column('confidence', sa.Numeric(), nullable=False),
        sa.Column('predicted_window_start', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('predicted_window_end', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['atm_id'], ['atms.atm_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prediction_id'], ['predictions.prediction_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('result_id')
    )

    # 7. prediction_features (result_id FK -> prediction_results.result_id)
    op.create_table(
        'prediction_features',
        sa.Column('feature_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('result_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feature_name', sa.String(), nullable=False),
        sa.Column('feature_value', sa.Numeric(), nullable=False),
        sa.Column('contribution', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['result_id'], ['prediction_results.result_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('feature_id')
    )

    # 8. alerts
    op.create_table(
        'alerts',
        sa.Column('alert_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('prediction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('atm_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['atm_id'], ['atms.atm_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prediction_id'], ['predictions.prediction_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('alert_id')
    )

    # 9. users
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('user_id')
    )

    # 10. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('resource', sa.String(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('event_id')
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('alerts')
    op.drop_table('prediction_features')
    op.drop_table('prediction_results')
    op.drop_table('predictions')
    op.drop_table('model_metadata')
    op.drop_table('transactions')
    op.drop_table('atms')
    op.drop_table('crimes')

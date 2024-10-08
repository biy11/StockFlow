"""Add DailyOrder table

Revision ID: 8164dcf1174b
Revises: f8797fd777ab
Create Date: 2024-09-25 13:34:35.452159

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8164dcf1174b'
down_revision = 'f8797fd777ab'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('daily_order',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_no', sa.String(length=50), nullable=False),
    sa.Column('customer_name', sa.String(length=100), nullable=False),
    sa.Column('delivery_comment', sa.String(length=255), nullable=True),
    sa.Column('date_assigned', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('daily_order')
    # ### end Alembic commands ###

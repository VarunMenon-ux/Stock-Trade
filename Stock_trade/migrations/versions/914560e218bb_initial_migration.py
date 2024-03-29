"""Initial migration

Revision ID: 914560e218bb
Revises: 
Create Date: 2023-03-20 07:04:08.160954

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '914560e218bb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('market_hours',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('open_time', sa.Time(), nullable=True),
    sa.Column('close_time', sa.Time(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('market_schedule', schema=None) as batch_op:
        batch_op.add_column(sa.Column('start_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('end_date', sa.Date(), nullable=True))
        batch_op.alter_column('days_open',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=100),
               existing_nullable=True)
        batch_op.drop_column('close_time')
        batch_op.drop_column('open_time')

    with op.batch_alter_table('trade', schema=None) as batch_op:
        batch_op.add_column(sa.Column('total_value', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('trade', schema=None) as batch_op:
        batch_op.drop_column('total_value')

    with op.batch_alter_table('market_schedule', schema=None) as batch_op:
        batch_op.add_column(sa.Column('open_time', sa.TIME(), nullable=True))
        batch_op.add_column(sa.Column('close_time', sa.TIME(), nullable=True))
        batch_op.alter_column('days_open',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=20),
               existing_nullable=True)
        batch_op.drop_column('end_date')
        batch_op.drop_column('start_date')

    op.drop_table('market_hours')
    # ### end Alembic commands ###

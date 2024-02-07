"""removed ticker

Revision ID: ea9ad5953dad
Revises: 58454641bbc0
Create Date: 2023-03-21 09:19:38.456599

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea9ad5953dad'
down_revision = '58454641bbc0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('stock', schema=None) as batch_op:
        batch_op.drop_index('ix_stock_ticker')
        batch_op.drop_column('ticker')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('stock', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ticker', sa.VARCHAR(length=10), nullable=True))
        batch_op.create_index('ix_stock_ticker', ['ticker'], unique=False)

    # ### end Alembic commands ###
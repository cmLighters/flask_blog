"""empty message

Revision ID: f85b7de6788e
Revises: 
Create Date: 2018-03-05 21:05:52.066609

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f85b7de6788e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('password_hash', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'password_hash')
    # ### end Alembic commands ###

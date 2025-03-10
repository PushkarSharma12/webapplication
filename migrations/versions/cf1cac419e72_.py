"""empty message

Revision ID: cf1cac419e72
Revises: 9d542698cd90
Create Date: 2020-08-16 12:32:42.507513

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf1cac419e72'
down_revision = '9d542698cd90'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('diary',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_per_user', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=25), nullable=False),
    sa.Column('content', sa.String(length=999), nullable=False),
    sa.Column('topic', sa.String(length=999), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('diary')
    # ### end Alembic commands ###

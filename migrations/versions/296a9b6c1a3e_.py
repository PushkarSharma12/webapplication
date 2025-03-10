"""empty message

Revision ID: 296a9b6c1a3e
Revises: 
Create Date: 2020-08-16 09:05:56.629357

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '296a9b6c1a3e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('friends')
    op.drop_table('diary')
    op.drop_table('users')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('users_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('username', sa.VARCHAR(length=25), autoincrement=False, nullable=False),
    sa.Column('email', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('passworrd', sa.TEXT(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='users_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('diary',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('diary_sequence'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('username', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('id_per_user', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('topic', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('date', sa.DATE(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='diary_pkey')
    )
    op.create_table('friends',
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('friend_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['friend_id'], ['users.id'], name='friends_friend_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='friends_user_id_fkey')
    )
    # ### end Alembic commands ###

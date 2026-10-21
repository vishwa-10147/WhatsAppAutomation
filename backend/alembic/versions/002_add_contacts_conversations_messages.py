"""Add contacts, conversations, messages, templates tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create contacts table
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phone_number', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('is_opted_in', sa.Boolean(), nullable=False, default=True),
        sa.Column('opted_in_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opted_out_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('custom_fields', sa.Text(), nullable=True),
        sa.Column('last_interaction_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'phone_number', name='uq_contacts_org_phone_number'),
    )
    op.create_index('ix_contact_org_last_interaction', 'contacts', ['organization_id', 'last_interaction_at'])
    op.create_index('ix_contact_org_name', 'contacts', ['organization_id', 'name'])
    op.create_index('ix_contacts_organization_id', 'contacts', ['organization_id'])
    op.create_index('ix_contacts_phone_number', 'contacts', ['phone_number'])

    # Create contact_tags table
    op.create_table(
        'contact_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'contact_id', 'name', name='uq_org_contact_tag'),
    )

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assignee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('open', 'pending', 'resolved', name='conversation_status', native_enum=False), nullable=False, default='open'),
        sa.Column('unread_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_data', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_conversation_org_last_message', 'conversations', ['organization_id', 'last_message_at'])
    op.create_index('ix_conversation_org_status', 'conversations', ['organization_id', 'status'])
    op.create_index('ix_conversations_contact_id', 'conversations', ['contact_id'])
    op.create_index('ix_conversations_organization_id', 'conversations', ['organization_id'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('whatsapp_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('direction', sa.Enum('inbound', 'outbound', name='message_direction', native_enum=False), nullable=False),
        sa.Column('type', sa.Enum('text', 'image', 'document', 'audio', 'video', 'template', 'interactive', name='message_type', native_enum=False), nullable=False),
        sa.Column('content', sa.Text(), nullable=False, default=''),
        sa.Column('media_id', sa.String(length=255), nullable=True),
        sa.Column('media_url', sa.Text(), nullable=True),
        sa.Column('media_mime_type', sa.String(length=100), nullable=True),
        sa.Column('media_filename', sa.String(length=255), nullable=True),
        sa.Column('template_name', sa.String(length=255), nullable=True),
        sa.Column('template_language', sa.String(length=10), nullable=True),
        sa.Column('status', sa.Enum('sent', 'delivered', 'read', 'failed', name='message_status', native_enum=False), nullable=False, default='sent'),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['whatsapp_account_id'], ['whatsapp_accounts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'external_id', name='uq_org_external_id'),
    )
    op.create_index('ix_message_conversation', 'messages', ['conversation_id', 'sent_at'])
    op.create_index('ix_message_org_direction', 'messages', ['organization_id', 'direction'])
    op.create_index('ix_message_org_sent', 'messages', ['organization_id', 'sent_at'])
    op.create_index('ix_message_org_status', 'messages', ['organization_id', 'status'])
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_external_id', 'messages', ['external_id'])
    op.create_index('ix_messages_organization_id', 'messages', ['organization_id'])

    # Create message_templates table
    op.create_table(
        'message_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False, default='en_US'),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('header_type', sa.String(length=50), nullable=True),
        sa.Column('header_text', sa.Text(), nullable=True),
        sa.Column('header_media_id', sa.String(length=255), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('footer_text', sa.Text(), nullable=True),
        sa.Column('buttons', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='template_status', native_enum=False), nullable=False, default='pending'),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('rejected_reason', sa.Text(), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'name', 'language', name='uq_org_template_name_lang'),
    )
    op.create_index('ix_message_templates_organization_id', 'message_templates', ['organization_id'])


def downgrade() -> None:
    op.drop_table('message_templates')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('contact_tags')
    op.drop_table('contacts')

    op.execute('DROP TYPE IF EXISTS conversation_status')
    op.execute('DROP TYPE IF EXISTS message_direction')
    op.execute('DROP TYPE IF EXISTS message_type')
    op.execute('DROP TYPE IF EXISTS message_status')
    op.execute('DROP TYPE IF EXISTS template_status')
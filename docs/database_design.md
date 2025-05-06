# Database Schema Design

This document outlines the database schema design for the MT 9 EMA Backtester community features, focusing on optimal query patterns, scalability, and data integrity.

## Overview

The database schema design for the MT 9 EMA Backtester's community features is built to support efficient data access patterns, scale from dozens to thousands of users, and maintain data integrity across the application. The design prioritizes:

1. **Performance**: Optimized for common query patterns
2. **Scalability**: Designed to handle growth in users and content
3. **Integrity**: Strong relationships to prevent data inconsistencies
4. **Flexibility**: Adaptable to evolving feature requirements

## Core Tables

### User Management

User-related tables manage authentication, profiles, and permissions:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `users` | Core user accounts | `user_id`, `username`, `email`, `password_hash` |
| `user_profiles` | Extended user information | `user_id`, `bio`, `location`, `preferences` |
| `user_roles` | Role assignments | `user_id`, `role`, `granted_at` |
| `user_achievements` | User achievements | `user_id`, `achievement_id`, `achieved_at` |

### Community Forum

Forum functionality is implemented with these tables:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `forum_categories` | Forum organization structure | `category_id`, `name`, `description` |
| `forum_topics` | Discussion topics | `topic_id`, `category_id`, `user_id`, `title` |
| `forum_posts` | Individual posts | `post_id`, `topic_id`, `user_id`, `content` |
| `post_reactions` | Likes, awards, etc. | `post_id`, `user_id`, `reaction_type` |

### Trading Setup Sharing

Tables for sharing trading strategies and setups:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `trading_setups` | Shared strategies | `setup_id`, `user_id`, `title`, `parameters` |
| `setup_comments` | Comments on setups | `comment_id`, `setup_id`, `user_id`, `content` |
| `setup_likes` | Setup appreciations | `setup_id`, `user_id`, `created_at` |

### Trading Signals

Tables for sharing trading signals and signal subscriptions:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `trading_signals` | Trading signals | `signal_id`, `user_id`, `symbol`, `entry_price` |
| `signal_subscriptions` | Signal subscriptions | `user_id`, `provider_id`, `subscription_level` |

## Table Relationships

### Entity-Relationship Diagram

Below is a simplified entity-relationship diagram showing key relationships:

```
users 1──┐
         ├─ * user_profiles
         ├─ * user_roles
         ├─ * user_achievements
         │
         ├─ * forum_topics ─ * forum_posts ─ * post_reactions
         │                    │
         │                    └─────────────┐
         │                                  │
         ├─ * trading_setups ─ * setup_comments
         │   │                 
         │   └─ * setup_likes
         │
         ├─ * trading_signals
         │
         └─ * signal_subscriptions
```

### Key Relationships

- Each user can have multiple roles, achievements, and a single profile
- Users create forum topics containing multiple posts
- Users create trading setups that can receive comments and likes
- Users publish trading signals that others can subscribe to

## Optimized Query Patterns

The schema is optimized for these common query patterns:

### User Feed Generation

```sql
-- Get personalized feed items for a user
SELECT * FROM (
    -- Recent forum posts in followed categories
    SELECT fp.post_id as content_id, 'forum_post' as content_type, fp.created_at
    FROM forum_posts fp
    JOIN forum_topics ft ON fp.topic_id = ft.topic_id
    JOIN forum_categories fc ON ft.category_id = fc.category_id
    JOIN category_subscriptions cs ON cs.category_id = fc.category_id
    WHERE cs.user_id = :user_id AND fp.status = 'published'
    
    UNION ALL
    
    -- Recent trading setups from followed users
    SELECT ts.setup_id as content_id, 'trading_setup' as content_type, ts.created_at
    FROM trading_setups ts
    JOIN user_follows uf ON ts.user_id = uf.followed_id
    WHERE uf.follower_id = :user_id AND ts.status = 'published' AND ts.visibility = 'public'
    
    UNION ALL
    
    -- Recent signals from subscribed providers
    SELECT sg.signal_id as content_id, 'trading_signal' as content_type, sg.created_at
    FROM trading_signals sg
    JOIN signal_subscriptions ss ON sg.user_id = ss.provider_id
    WHERE ss.user_id = :user_id AND sg.status = 'active'
) AS combined
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset
```

### Performance Leaderboard

```sql
-- Get trader performance leaderboard
SELECT u.user_id, u.username, u.profile_picture_url, 
       pm.win_rate, pm.profit_factor, pm.total_trades, pm.avg_trade
FROM performance_metrics pm
JOIN users u ON pm.user_id = u.user_id
WHERE pm.timeframe = :timeframe AND pm.period = :period
ORDER BY pm.profit_factor DESC
LIMIT :limit OFFSET :offset
```

### Topic with Posts

```sql
-- Get forum topic details
SELECT * FROM forum_topics WHERE topic_id = :topic_id;

-- Get paginated posts with user info and reactions
SELECT fp.*, u.username, u.profile_picture_url, 
       (SELECT COUNT(*) FROM post_reactions pr WHERE pr.post_id = fp.post_id AND pr.reaction_type = 'like') as like_count
FROM forum_posts fp
JOIN users u ON fp.user_id = u.user_id
WHERE fp.topic_id = :topic_id AND fp.status = 'published'
ORDER BY fp.created_at
LIMIT :limit OFFSET :offset
```

## Indexing Strategy

The database uses specialized indexes to optimize performance:

### B-Tree Indexes

Standard B-tree indexes are used for equality and range queries:

```sql
-- Primary key and foreign key indexes
CREATE INDEX idx_forum_posts_topic_id ON forum_posts(topic_id);
CREATE INDEX idx_trading_setups_user_id ON trading_setups(user_id);

-- Composite indexes for common query patterns
CREATE INDEX idx_forum_posts_topic_created ON forum_posts(topic_id, created_at);
CREATE INDEX idx_trading_signals_status_created ON trading_signals(status, created_at);
```

### Specialized Indexes

For more complex use cases:

```sql
-- Full-text search on forum content
CREATE INDEX idx_forum_posts_fulltext ON forum_posts 
USING gin(to_tsvector('english', content));

-- Tag searching for trading setups
CREATE INDEX idx_trading_setups_tags ON trading_setups
USING gin(tags);

-- Partial indexes for active content
CREATE INDEX idx_active_signals ON trading_signals(user_id, created_at)
WHERE status = 'active';
```

## Scalability Considerations

The schema includes design patterns for scaling to thousands of users:

### Partitioning Strategy

Large tables are partitioned for better performance:

```sql
-- Partition forum posts by creation date
CREATE TABLE forum_posts (
    post_id UUID PRIMARY KEY,
    topic_id UUID,
    user_id UUID,
    content TEXT,
    created_at TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE forum_posts_y2023m01 PARTITION OF forum_posts
FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');
```

### Denormalization

Strategic denormalization improves read performance:

```sql
-- Denormalized view of topics with statistics
CREATE MATERIALIZED VIEW forum_topics_with_stats AS
SELECT 
    t.*,
    c.name AS category_name,
    c.slug AS category_slug,
    u.username AS author_username,
    u.profile_picture_url,
    (SELECT COUNT(*) FROM forum_posts WHERE topic_id = t.topic_id) AS post_count,
    lp.created_at AS last_post_at,
    lu.username AS last_post_author
FROM forum_topics t
JOIN forum_categories c ON t.category_id = c.category_id
JOIN users u ON t.user_id = u.user_id
LEFT JOIN forum_posts lp ON t.last_post_id = lp.post_id
LEFT JOIN users lu ON lp.user_id = lu.user_id;
```

### Sharding Strategy

For future growth, tables can be sharded:

```
User Data Sharding:
- Shard Key: user_id
- Algorithm: Consistent Hashing
- Tables: users, user_profiles, user_activity, notifications

Content Data Sharding:
- Shard Key: created_at
- Algorithm: Range-based
- Tables: forum_posts, trading_signals, trading_setups
```

## Data Integrity

Several mechanisms ensure data integrity:

### Constraints

Foreign key constraints maintain relationships:

```sql
-- Example constraints on forum_posts
ALTER TABLE forum_posts 
ADD CONSTRAINT fk_forum_posts_topic 
FOREIGN KEY (topic_id) REFERENCES forum_topics(topic_id)
ON DELETE CASCADE;

ALTER TABLE forum_posts
ADD CONSTRAINT fk_forum_posts_user
FOREIGN KEY (user_id) REFERENCES users(user_id)
ON DELETE SET NULL;
```

### Soft Deletion

Content is soft-deleted to maintain referential integrity:

```sql
-- Soft delete patterns
UPDATE forum_posts SET status = 'deleted', deleted_at = NOW() WHERE post_id = :post_id;
```

### Triggers

Triggers maintain derived data:

```sql
-- Update last_post_id and last_post_at when a new post is created
CREATE TRIGGER update_topic_last_post
AFTER INSERT ON forum_posts
FOR EACH ROW
EXECUTE FUNCTION update_topic_last_post_func();
```

## Implementation for Developers

### Recommended ORM Setup

The schema works well with SQLAlchemy for Python applications:

```python
# Example SQLAlchemy model for forum topics
class ForumTopic(Base):
    __tablename__ = "forum_topics"
    
    topic_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, ForeignKey("forum_categories.category_id"))
    user_id = Column(String, ForeignKey("users.user_id"))
    title = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    status = Column(String, default="published")
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    last_post_id = Column(String, ForeignKey("forum_posts.post_id"), nullable=True)
    last_post_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("ForumCategory", back_populates="topics")
    user = relationship("User", back_populates="topics")
    posts = relationship("ForumPost", back_populates="topic")
```

### Query Examples

Common data access patterns:

```python
# Get recent topics with post count
def get_recent_topics(category_id=None, limit=20):
    query = (
        session.query(
            ForumTopic,
            func.count(ForumPost.post_id).label("post_count")
        )
        .join(ForumTopic.posts)
        .filter(ForumTopic.status == "published")
        .group_by(ForumTopic.topic_id)
        .order_by(ForumTopic.last_post_at.desc())
        .limit(limit)
    )
    
    if category_id:
        query = query.filter(ForumTopic.category_id == category_id)
        
    return query.all()
```

## Database Evolution

### Migration Strategy

Database changes follow these principles:

1. **Non-destructive Changes**: Add, don't remove or repurpose columns
2. **Versioned Migrations**: Every schema change has a migration script
3. **Backwards Compatibility**: New code works with old schema during transition
4. **Feature Flags**: New schema elements hidden behind feature flags until ready

### Sample Migration

```python
# Example Alembic migration
def upgrade():
    op.add_column('trading_signals', 
                 sa.Column('risk_reward_ratio', sa.Numeric(10, 2)))
    op.create_index(op.f('ix_trading_signals_risk_reward'), 
                   'trading_signals', ['risk_reward_ratio'])

def downgrade():
    op.drop_index(op.f('ix_trading_signals_risk_reward'), 
                 table_name='trading_signals')
    op.drop_column('trading_signals', 'risk_reward_ratio')
```

## Performance Guidelines

Recommendations for maximizing database performance:

1. **Limit Result Sets**: Always include LIMIT clauses
2. **Use Prepared Statements**: Reuse query plans for similar queries
3. **Batch Operations**: Use bulk inserts/updates for better throughput
4. **Lazy Loading**: Avoid loading unnecessary related data
5. **Connection Pooling**: Reuse database connections
6. **Monitor Query Performance**: Regularly analyze slow queries

## Future Schema Enhancements

Planned improvements to the schema:

1. **Versioned Content**: Track changes to setups and signals
2. **Activity Streams**: Optimized activity feed generation
3. **Recommendation System**: Tables for personalized content recommendations
4. **Geospatial Features**: Support for location-aware trading communities
5. **Advanced Analytics**: Schema support for ML-based trade analysis 
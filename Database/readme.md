Database Management Systems — What I Did and What I Learned
-----------------------------------------------------------

### 1\. DBMS Final Project — AI Expense Tracker

This project represents my **hands-on implementation of core database management system concepts** through a complete, working application.

The goal of the project was to design and build a **privacy-first expense tracking system** that goes beyond basic CRUD operations and demonstrates **real database reasoning, optimization, and analytics**.

#### What Was Done in the Project

At the database level, the project includes:

*   **Relational data modeling**
    
    *   Designed an Entity–Relationship (ER) model
        
    *   Converted ERD into a **normalized relational schema**
        
    *   Tables for users, transactions, categories, budgets, and summaries
        
*   **Schema design and normalization**
    
    *   Removed redundancy
        
    *   Ensured data integrity through proper keys and relationships
        
*   **CRUD operations**
    
    *   Insert, update, delete, and query expense and budget data
        
    *   Implemented using SQLAlchemy with a Python backend
        
*   **Transaction management**
    
    *   Used atomic transactions to ensure consistency when:
        
        *   Logging expenses
            
        *   Updating budgets
            
    *   Demonstrated ACID properties, especially **atomicity and consistency**
        
*   **SQL analytics**
    
    *   Wrote multiple analytical SQL queries:
        
        *   Monthly spending summaries
            
        *   Category-wise breakdowns
            
        *   Budget vs actual comparisons
            
    *   Identified overspending periods
        
*   **Indexing and query optimization**
    
    *   Created indexes on frequently queried fields (user, date, category)
        
    *   Compared query performance **before and after indexing**
        
    *   Used query plans (EXPLAIN) to reason about performance
        
*   **Advanced features**
    
    *   Retrieval-Augmented Generation (RAG) for natural-language questions
        
    *   Anomaly detection to identify unusual spending patterns
        
    *   Simple clustering to group spending behavior
        

This project demonstrates how **database theory translates into a real system**, not just SQL scripts.

### 2\. Research Paper Reading — Personal Health Agent (PHA)

As part of the course, I also studied and presented a **research paper published by Google Research (2025)** on **Personal Health Agents**.

This paper focuses on how **modern data-driven systems use databases, analytics, and AI together**, rather than in isolation.

#### What I Learned from the Paper

From the Personal Health Agent paper, I learned:

*   How **data pipelines** feed into intelligent systems
    
*   The role of structured data, time-series data, and historical records
    
*   Why **data quality, grounding, and explainability** matter
    
*   How multi-agent systems rely on:
    
    *   Well-structured storage
        
    *   Queryable summaries
        
    *   Reliable data access layers
        
*   How databases support:
    
    *   Personalization
        
    *   Longitudinal user history
        
    *   Trust and accountability in AI systems
        

This strengthened my understanding of how **databases are foundational to AI systems**, not just storage components.

### 3\. Database Internals Study — LSM Trees

I also studied **Log-Structured Merge (LSM) Trees**, which are widely used in modern databases such as RocksDB, Cassandra, and LevelDB.

This was not just surface-level knowledge but focused on **why modern databases are designed this way**.

#### Key Concepts Learned

*   Why traditional B-trees struggle with **write-heavy workloads**
    
*   How LSM trees:
    
    *   Convert random writes into sequential writes
        
    *   Use memtables and SSTables
        
*   Understanding of:
    
    *   Compaction
        
    *   Leveling vs tiering
        
    *   Read amplification vs write amplification
        
*   Read optimization techniques:
    
    *   Bloom filters
        
    *   Fence pointers
        
    *   Block caches
        
*   Why database tuning is a **trade-off problem**, not a fixed solution
    
*   How modern databases dynamically adapt to workload changes
    

This helped me understand **what happens under the hood** of real database systems.

### 4\. Overall Database Concepts I Learned

By combining the **project implementation**, **paper reading**, and **database internals study**, I developed a strong understanding of:

*   **Relational database design**
    
    *   Translating real-world requirements into relational models
        
    *   Designing schemas that balance clarity, extensibility, and performance
        
*   **Normalization and schema design**
    
    *   Applying normalization principles (1NF–3NF) to eliminate redundancy
        
    *   Understanding when controlled denormalization is beneficial for performance
        
*   **SQL querying and analytics**
    
    *   Writing complex analytical queries using joins, aggregations, and subqueries
        
    *   Designing queries for reporting, trend analysis, and business insights
        
*   **Indexing and performance optimization**
    
    *   Choosing appropriate index types based on query patterns
        
    *   Understanding trade-offs between write performance and read efficiency
        
    *   Interpreting query execution plans to reason about performance
        
*   **Transaction management and ACID properties**
    
    *   Implementing atomic operations across multiple tables
        
    *   Understanding isolation, consistency, and durability in real systems
        
    *   Preventing partial updates and data corruption
        
*   **Concurrency and consistency concepts**
    
    *   How databases handle concurrent reads and writes
        
    *   Basic understanding of locking, isolation levels, and race conditions
        
    *   Why consistency models matter in multi-user systems
        
*   **How databases support real applications**
    
    *   Managing persistent state for user-facing systems
        
    *   Supporting analytics, reporting, and auditing
        
    *   Designing databases that evolve with application requirements
        
*   **Database internals and storage engines**
    
    *   Understanding how data is stored on disk and in memory
        
    *   Differences between B-tree–based and LSM-based storage engines
        
    *   Write amplification, read amplification, and compaction trade-offs
        
*   **Modern database architectures**
    
    *   Separation of storage and query layers
        
    *   Use of caching, buffers, and filters to improve performance
        
    *   How databases scale with increasing data volume and workload
        
*   **Integration of databases with AI and analytics systems**
    
    *   Using structured data as input for analytical pipelines
        
    *   Supporting natural-language querying through RAG-style systems
        
    *   Ensuring data grounding, explainability, and traceability in AI outputs
        
*   **Data quality, reliability, and trust**
    
    *   Importance of clean, validated data for analytics and decision-making
        
    *   Role of constraints and schema design in preventing bad data
        
    *   Why databases are foundational to trustworthy AI systems
        
*   **Engineering mindset for database systems**
    
    *   Thinking in terms of trade-offs rather than “one best design”
        
    *   Designing systems that are correct first, then optimized
        
    *   Understanding how theory informs practical engineering decisions
        

### Big Picture Takeaway

This DBMS coursework moved me from **“writing SQL queries”** to **thinking like a database engineer**.

I now understand:

*   Why schemas are designed a certain way
    
*   How performance depends on indexing and access patterns
    
*   Why internal data structures (like LSM trees) matter
    
*   How databases power modern AI-driven systems
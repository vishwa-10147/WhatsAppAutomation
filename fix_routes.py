with open('backend/app/api/routes/workflows.py', 'rb') as f:
    content = f.read()

old = b'for w in workflows\n    ]\n\n\n\n\n\n@router.get("/{workflow_id}", response_model=WorkflowDetailResponse)'

new = b'''for w in workflows
    ]


# ==================== SCHEDULED JOBS ====================

@router.post("/scheduled-jobs", response_model=ScheduledJobResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_job(
    data: ScheduledJobCreate,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    engine = WorkflowEngine(session, UUID(org_id))
    job = await engine.create_scheduled_job(
        workflow_id=data.workflow_id,
        name=data.name,
        cron_expression=data.cron_expression,
        run_once_at=datetime.fromisoformat(data.run_once_at) if data.run_once_at else None,
        timezone=data.timezone,
        trigger_data=data.trigger_data,
        max_runs=data.max_runs,
    )

    return ScheduledJobResponse(
        id=job.id,
        workflow_id=job.workflow_id,
        name=job.name,
        cron_expression=job.cron_expression,
        run_once_at=job.run_once_at.isoformat() if job.run_once_at else None,
        timezone=job.timezone,
        trigger_data=job.trigger_data,
        status=job.status,
        next_run_at=job.next_run_at.isoformat() if job.next_run_at else None,
        last_run_at=job.last_run_at.isoformat() if job.last_run_at else None,
        run_count=job.run_count,
        max_runs=job.max_runs,
        is_active=job.is_active,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
    )


@router.get("/scheduled-jobs", response_model=List[ScheduledJobResponse])
async def list_scheduled_jobs(
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
    active_only: bool = Query(True),
):
    from uuid import UUID

    query = select(ScheduledJob).where(ScheduledJob.organization_id == UUID(org_id))
    if active_only:
        query = query.where(ScheduledJob.is_active == True)
    query = query.order_by(desc(ScheduledJob.created_at))

    result = await session.execute(query)
    jobs = result.scalars().all()

    return [
        ScheduledJobResponse(
            id=j.id,
            workflow_id=j.workflow_id,
            name=j.name,
            cron_expression=j.cron_expression,
            run_once_at=j.run_once_at.isoformat() if j.run_once_at else None,
            timezone=j.timezone,
            trigger_data=j.trigger_data,
            status=j.status,
            next_run_at=j.next_run_at.isoformat() if j.next_run_at else None,
            last_run_at=j.last_run_at.isoformat() if j.last_run_at else None,
            run_count=j.run_count,
            max_runs=j.max_runs,
            is_active=j.is_active,
            created_at=j.created_at.isoformat(),
            updated_at=j.updated_at.isoformat(),
        )
        for j in jobs
    ]


@router.delete("/scheduled-jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_job(
    job_id: UUID,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(ScheduledJob).where(
            and_(
                ScheduledJob.id == job_id,
                ScheduledJob.organization_id == UUID(org_id),
            )
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")

    await session.delete(job)
    await session.commit()


@router.get("/{workflow_id}", response_model=WorkflowDetailResponse)'''

if old in content:
    content = content.replace(old, new)
    with open('backend/app/api/routes/workflows.py', 'wb') as f:
        f.write(content)
    print("SUCCESS: Replaced")
else:
    print("OLD STRING NOT FOUND")
    print("Expected:", repr(old))
    idx = content.find(b'for w in workflows')
    print("Found at idx:", idx)
    if idx >= 0:
        print("Found:", repr(content[idx:idx+100]))
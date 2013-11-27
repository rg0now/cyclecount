loop_i=LOOP_COUNT;
loop_i2=BITS*10000;
while(--loop_i > 0)
{
	while(--loop_i2 > 0)
	{
		apple ^= banana ^ loop_i2;
		apple *= banana + loop_i2;
	}
}

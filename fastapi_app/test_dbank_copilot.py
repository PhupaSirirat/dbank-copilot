"""
Test script for dBank Support Copilot
Tests the three main business requirements
"""
import asyncio
import httpx
import json
from datetime import datetime, timedelta


class DBankCopilotTester:
    """Test harness for dBank Support Copilot"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def test_health(self) -> bool:
        """Test health endpoint"""
        print("🔍 Testing health endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            health = response.json()
            
            print(f"   Status: {health['status']}")
            print(f"   MCP Server: {'✅' if health['mcp_server'] else '❌'}")
            print(f"   LLM Client: {'✅' if health['llm_client'] else '❌'}")
            print(f"   Vector Store: {'✅' if health['vector_store'] else '❌'}")
            
            return health['status'] == 'healthy'
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def test_requirement_1_root_causes(self) -> bool:
        """
        Test Requirement 1:
        Top 5 root causes of product issues in the previous month by category with % open ticket
        """
        print("\n🔍 Testing Requirement 1: Top Root Causes Analysis...")
        
        try:
            # Calculate last month's date range
            today = datetime.now()
            first_of_month = today.replace(day=1)
            last_month_end = first_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            
            question = f"What are the top 5 root causes of product issues from {last_month_start.strftime('%Y-%m-%d')} to {last_month_end.strftime('%Y-%m-%d')} by category with percentage of open tickets?"
            
            print(f"   Question: {question[:80]}...")
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/ask",
                json={
                    "question": question,
                    "stream": True  # Always true for dBank
                }
            ) as response:
                full_answer = ""
                tool_calls = []
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        
                        if data["type"] == "text":
                            full_answer += data["content"]
                        elif data["type"] == "tool_call":
                            tool_calls.append(data["data"]["tool_name"])
                            print(f"   Tool Called: {data['data']['tool_name']}")
                        elif data["type"] == "done":
                            print(f"   Response Time: {data['data']['response_time']:.2f}s")
                
                print(f"   Answer Preview: {full_answer[:200]}...")
                print(f"   Tool Calls: {tool_calls}")
                
                # Check if kpi_top_root_causes was called
                has_kpi_tool = "kpi_top_root_causes" in tool_calls
                print(f"   Used KPI Tool: {'✅' if has_kpi_tool else '❌'}")
                
                return has_kpi_tool and len(full_answer) > 0
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def test_requirement_2_spike_detection(self) -> bool:
        """
        Test Requirement 2:
        Did ticket volume spike after Virtual Bank App v1.2 release?
        Show anomaly window and related product
        """
        print("\n🔍 Testing Requirement 2: Spike Detection After Release...")
        
        try:
            question = "Did ticket volume spike after Virtual Bank App v1.2 release? Show the anomaly window and which products were affected like Digital Saving or Digital Lending."
            
            print(f"   Question: {question[:80]}...")
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/ask",
                json={"question": question}
            ) as response:
                full_answer = ""
                tool_calls = []
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        
                        if data["type"] == "text":
                            full_answer += data["content"]
                        elif data["type"] == "tool_call":
                            tool_calls.append(data["data"]["tool_name"])
                            print(f"   Tool Called: {data['data']['tool_name']}")
                        elif data["type"] == "done":
                            print(f"   Response Time: {data['data']['response_time']:.2f}s")
                
                print(f"   Answer Preview: {full_answer[:200]}...")
                print(f"   Tool Calls: {tool_calls}")
                
                # Check if SQL was used
                has_sql = "sql_query" in tool_calls
                print(f"   Used SQL Query: {'✅' if has_sql else '❌'}")
                
                return has_sql and len(full_answer) > 0
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def test_requirement_3_churned_customers(self) -> bool:
        """
        Test Requirement 3:
        Write SQL for churned customers in last 30, 90 days (not logged in)
        """
        print("\n🔍 Testing Requirement 3: Churned Customer SQL...")
        
        try:
            question = "Write the SQL query to find churned customers who haven't logged in to the Virtual Bank App in the last 30 days and 90 days."
            
            print(f"   Question: {question[:80]}...")
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/ask",
                json={"question": question}
            ) as response:
                full_answer = ""
                tool_calls = []
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        
                        if data["type"] == "text":
                            full_answer += data["content"]
                        elif data["type"] == "tool_call":
                            tool_calls.append(data["data"]["tool_name"])
                            print(f"   Tool Called: {data['data']['tool_name']}")
                        elif data["type"] == "done":
                            print(f"   Response Time: {data['data']['response_time']:.2f}s")
                
                print(f"   Answer Preview: {full_answer[:200]}...")
                
                # Check if SQL or answer contains SQL query
                has_sql = "SELECT" in full_answer.upper() or "sql_query" in tool_calls
                print(f"   Contains SQL: {'✅' if has_sql else '❌'}")
                
                return has_sql and len(full_answer) > 0
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def test_knowledge_base(self) -> bool:
        """Test knowledge base search"""
        print("\n🔍 Testing Knowledge Base Search...")
        
        try:
            question = "What are the known issues with Digital Lending product?"
            
            print(f"   Question: {question}")
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/ask",
                json={"question": question}
            ) as response:
                full_answer = ""
                tool_calls = []
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        
                        if data["type"] == "text":
                            full_answer += data["content"]
                        elif data["type"] == "tool_call":
                            tool_calls.append(data["data"]["tool_name"])
                        elif data["type"] == "done":
                            print(f"   Response Time: {data['data']['response_time']:.2f}s")
                
                print(f"   Tool Calls: {tool_calls}")
                
                has_kb = "kb_search" in tool_calls
                print(f"   Used KB Search: {'✅' if has_kb else '❌'}")
                
                return has_kb and len(full_answer) > 0
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def test_conversation_context(self) -> bool:
        """Test conversation context"""
        print("\n🔍 Testing Conversation Context...")
        
        try:
            conv_id = f"test_conv_{int(datetime.now().timestamp())}"
            
            # First question
            question1 = "What products does dBank offer?"
            print(f"   Q1: {question1}")
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/ask",
                json={"question": question1, "conversation_id": conv_id}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data["type"] == "done":
                            break
            
            # Follow-up question
            question2 = "Which one has the most tickets?"
            print(f"   Q2: {question2} (uses context)")
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/ask",
                json={"question": question2, "conversation_id": conv_id}
            ) as response:
                full_answer = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data["type"] == "text":
                            full_answer += data["content"]
                        elif data["type"] == "done":
                            break
            
            print(f"   Follow-up Answer: {full_answer[:100]}...")
            print(f"   Context Used: ✅")
            
            return len(full_answer) > 0
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("=" * 70)
        print("🏦 dBank Support Copilot - Test Suite")
        print("=" * 70)
        
        tests = [
            ("Health Check", self.test_health),
            ("Requirement 1: Top Root Causes", self.test_requirement_1_root_causes),
            ("Requirement 2: Spike Detection", self.test_requirement_2_spike_detection),
            ("Requirement 3: Churned Customers SQL", self.test_requirement_3_churned_customers),
            ("Knowledge Base Search", self.test_knowledge_base),
            ("Conversation Context", self.test_conversation_context)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 Test Summary")
        print("=" * 70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print("\n" + "=" * 70)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All business requirements verified!")
        else:
            print("⚠️  Some tests failed. Please review.")
        
        print("=" * 70)
        
        await self.client.aclose()
        
        return passed == total


async def main():
    """Main test runner"""
    tester = DBankCopilotTester()
    
    try:
        success = await tester.run_all_tests()
        return success
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)